"""Verschlüsselte Dateiablage – Basisdienst für Kursräume, Postfach, Atteste (ARCHITECTURE.md §9.2).

Ablauf eines Uploads (``POST /api/v1/files`` bzw. :func:`store_bytes`): Die Daten werden in **einem** Durchlauf
blockweise gezählt (Größenlimit), gehasht (SHA-256), am Inhalt erkannt (Magic Bytes + Allowlist, aktive Inhalte
werden blockiert), optional an ClamAV gestreamt und mit eigenem Datenschlüssel verschlüsselt auf die Platte
geschrieben (``crypto.StreamEncryptor``, AAD = Datei-ID). Klartext landet nie auf der Platte; der Dateiname wird
verschlüsselt in der Datenbank gespeichert.

Für andere Features (Signaturen verbindlich)::

    from schulmanager.server import files
    meta = files.store_bytes(db, user, data, "brief.pdf", "application/pdf", "message_attachment")
    meta, data = files.read_file(db, file_id)                 # Klartext im Speicher (kleine Dateien)
    files.attach(db, file_id, user, "message", str(msg.id))   # nur eigene, noch nicht angehängte Dateien
    files.detach(db, file_id); files.delete(db, file_id)      # Bindung lösen / (weich) löschen
    files.register_access_check("message", fn)                # fn(db, user, stored_file) -> bool
    return files.file_response(meta, data, inline=False)      # sichere Download-Header
    files.file_info(meta, user)                               # JSON für Listen (FileList im Frontend)

Zugriff: Eigentümer immer; sonst NUR über die registrierte Prüfung des ``ref_type`` – es gibt bewusst **keinen**
automatischen Admin-Zugriff (Datenschutz: Atteste, Nachrichtenanhänge). Fehler sind :class:`FileError`
(= ``HTTPException`` mit ``detail = {"code", "message"}``) und können in Routen unverändert weitergeworfen werden.
"""
from __future__ import annotations

import codecs
import hashlib
import io
import logging
import os
import re
import socket
import struct
import threading
import time
import unicodedata
import uuid
import zipfile
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import crypto
from .config import config
from .db import iso, session_scope, utcnow
from .feature_models.files import StoredFile

log = logging.getLogger("schulmanager.files")

ORPHAN_HOURS = 24              # nicht angehängte Uploads werden danach gelöscht
PURGE_DAYS = 30                # gelöschte Dateien werden danach endgültig entfernt
BLOB_GC_HOURS = 12             # Abgleich Platte ↔ Datenbank höchstens so oft
STALE_TMP_HOURS = 6            # liegengebliebene Temp-Dateien
SMALL_FILE_BYTES = 8 * 1024 * 1024   # bis zu dieser Größe vor dem Senden vollständig geprüft
FORM_OVERHEAD = 1024 * 1024    # zusätzlich erlaubte Bytes für Multipart-Kopf/Felder
DEFAULT_PURPOSE = "general"
ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
PURPOSE_RE = re.compile(r"^[a-z][a-z0-9_.-]{1,39}$")
REF_TYPE_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,39}$")
UPLOAD_PERMISSIONS = frozenset({"messages.use", "channels.use", "channels.manage", "student_absence.report",
                                "student_documents.read", "masterdata.edit", "system.admin"})


# =========================================================================== Fehler
class FileError(HTTPException):
    """Fehler der Dateiablage (``HTTPException`` → kann direkt aus Routen kommen)."""

    def __init__(self, status_code: int, code: str, message: str, **extra: Any) -> None:
        super().__init__(status_code, {"code": code, "message": message, **extra})
        self.code = code
        self.message = message


def _not_found() -> FileError:
    return FileError(404, "not_found", "Datei nicht gefunden")


def _mb(n: float) -> str:
    return f"{n / 1024 / 1024:.1f}".replace(".", ",").replace(",0", "") + " MB"


# =========================================================================== Dateitypen (Allowlist)
@dataclass(frozen=True)
class FileKind:
    key: str
    label: str
    mime: str
    extensions: tuple[str, ...]      # erste = Standard-Endung
    group: str                       # document|image|office|text|audio|video|archive|app|code
    inline: bool = False             # darf im Browser angezeigt werden (nur PDF/Bilder, nie SVG)
    opt_in: bool = False             # nur für Zwecke, die die Art ausdrücklich freischalten (Quelltext)


# Quelltext (Informatik): nur als Download (text/plain, nie inline), nur für Zwecke mit ``extra_kinds=["code"]``
CODE_EXTENSIONS: tuple[str, ...] = (
    ".py", ".java", ".js", ".mjs", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".php", ".c", ".h",
    ".cpp", ".hpp", ".cc", ".cs", ".kt", ".swift", ".go", ".rs", ".rb", ".lua", ".r", ".m", ".sql", ".json",
    ".xml", ".yaml", ".yml", ".toml", ".ipynb", ".pde", ".ino", ".pas", ".dart", ".scala", ".hs", ".asm", ".s",
)


_KIND_LIST = (
    FileKind("pdf", "PDF-Dokument", "application/pdf", (".pdf",), "document", True),
    FileKind("png", "PNG-Bild", "image/png", (".png",), "image", True),
    FileKind("jpeg", "JPEG-Bild", "image/jpeg", (".jpg", ".jpeg", ".jpe", ".jfif"), "image", True),
    FileKind("gif", "GIF-Bild", "image/gif", (".gif",), "image", True),
    FileKind("webp", "WebP-Bild", "image/webp", (".webp",), "image", True),
    FileKind("heic", "HEIC-Foto", "image/heic", (".heic", ".heif"), "image", True),
    FileKind("svg", "SVG-Grafik (nur Download)", "image/svg+xml", (".svg",), "image", False),
    FileKind("tiff", "TIFF-Bild (nur Download)", "image/tiff", (".tif", ".tiff"), "image", False),
    FileKind("docx", "Word-Dokument", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
             (".docx", ".dotx"), "office"),
    FileKind("xlsx", "Excel-Tabelle", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             (".xlsx", ".xltx"), "office"),
    FileKind("pptx", "PowerPoint-Präsentation",
             "application/vnd.openxmlformats-officedocument.presentationml.presentation", (".pptx", ".ppsx", ".potx"),
             "office"),
    FileKind("odt", "OpenDocument-Text", "application/vnd.oasis.opendocument.text", (".odt", ".ott"), "office"),
    FileKind("ods", "OpenDocument-Tabelle", "application/vnd.oasis.opendocument.spreadsheet", (".ods", ".ots"),
             "office"),
    FileKind("odp", "OpenDocument-Präsentation", "application/vnd.oasis.opendocument.presentation", (".odp", ".otp"),
             "office"),
    FileKind("odg", "OpenDocument-Zeichnung", "application/vnd.oasis.opendocument.graphics", (".odg", ".otg"),
             "office"),
    FileKind("doc", "Word-Dokument (alt)", "application/msword", (".doc",), "office"),
    FileKind("xls", "Excel-Tabelle (alt)", "application/vnd.ms-excel", (".xls",), "office"),
    FileKind("ppt", "PowerPoint (alt)", "application/vnd.ms-powerpoint", (".ppt", ".pps"), "office"),
    FileKind("rtf", "RTF-Dokument", "application/rtf", (".rtf",), "office"),
    FileKind("epub", "E-Book (EPUB)", "application/epub+zip", (".epub",), "document"),
    FileKind("txt", "Textdatei", "text/plain", (".txt", ".text", ".log", ".tex", ".bib", ".srt", ".vtt"), "text"),
    FileKind("csv", "CSV-Tabelle", "text/csv", (".csv",), "text"),
    FileKind("md", "Markdown-Text", "text/markdown", (".md", ".markdown"), "text"),
    FileKind("mp3", "MP3-Audio", "audio/mpeg", (".mp3",), "audio"),
    FileKind("m4a", "M4A-Audio", "audio/mp4", (".m4a",), "audio"),
    FileKind("wav", "WAV-Audio", "audio/wav", (".wav",), "audio"),
    FileKind("ogg", "Ogg-Audio", "audio/ogg", (".ogg", ".oga", ".opus"), "audio"),
    FileKind("flac", "FLAC-Audio", "audio/flac", (".flac",), "audio"),
    FileKind("aac", "AAC-Audio", "audio/aac", (".aac",), "audio"),
    FileKind("midi", "MIDI-Datei", "audio/midi", (".mid", ".midi"), "audio"),
    FileKind("mp4", "MP4-Video", "video/mp4", (".mp4", ".m4v"), "video"),
    FileKind("mov", "QuickTime-Video", "video/quicktime", (".mov",), "video"),
    FileKind("webm", "WebM-Video", "video/webm", (".webm",), "video"),
    FileKind("avi", "AVI-Video", "video/x-msvideo", (".avi",), "video"),
    FileKind("mkv", "Matroska-Video", "video/x-matroska", (".mkv",), "video"),
    FileKind("mpeg", "MPEG-Video", "video/mpeg", (".mpg", ".mpeg"), "video"),
    FileKind("zip", "ZIP-Archiv", "application/zip", (".zip",), "archive"),
    # Unterrichtsprogramme (ZIP-Container mit eigener Endung – behalten ihren Namen, nur Download)
    FileKind("ggb", "GeoGebra-Datei", "application/vnd.geogebra.file", (".ggb",), "app"),
    FileKind("notebook", "SMART-Notebook", "application/x-smarttech-notebook", (".notebook",), "app"),
    FileKind("sb3", "Scratch-Projekt", "application/x.scratch.sb3", (".sb3", ".sb2"), "app"),
    FileKind("h5p", "H5P-Inhalt", "application/zip", (".h5p",), "app"),
    FileKind("code", "Quelltext (nur Download)", "text/plain", CODE_EXTENSIONS, "code", opt_in=True),
)
KINDS: dict[str, FileKind] = {k.key: k for k in _KIND_LIST}
GROUPS: dict[str, frozenset[str]] = {}
for _k in _KIND_LIST:
    GROUPS[_k.group] = GROUPS.get(_k.group, frozenset()) | {_k.key}
KNOWN_EXTENSIONS = frozenset(e for k in _KIND_LIST for e in k.extensions)
OPT_IN_KINDS = frozenset(k.key for k in _KIND_LIST if k.opt_in)
# ZIP-Container der Unterrichtsprogramme: Endung → (Art, Pflichteintrag im Archiv)
_CONTAINERS: dict[str, tuple[str, str]] = {".ggb": ("ggb", "geogebra.xml"), ".notebook": ("notebook", "imsmanifest.xml"),
                                           ".sb3": ("sb3", "project.json"), ".sb2": ("sb3", "project.json"),
                                           ".h5p": ("h5p", "h5p.json")}
# In Containern/E-Books zusätzlich erlaubt (Web-Inhalte der Programme, z. B. geogebra_javascript.js)
_CONTAINER_ALLOWED = frozenset({".js", ".mjs", ".html", ".htm", ".xhtml"})

# Endungen ausführbarer/aktiver Inhalte (Hochladen und Inhalt von ZIP-Archiven)
BLOCKED_EXTENSIONS = frozenset({
    ".exe", ".dll", ".com", ".bat", ".cmd", ".msi", ".msp", ".mst", ".scr", ".pif", ".cpl", ".sys", ".drv",
    ".ocx", ".js", ".mjs", ".cjs", ".jse", ".vbs", ".vbe", ".wsf", ".wsh", ".ws", ".hta", ".ps1", ".psm1",
    ".psd1", ".ps1xml", ".jar", ".class", ".apk", ".aab", ".ipa", ".app", ".appx", ".appxbundle", ".msix",
    ".msixbundle", ".lnk", ".url", ".scf", ".reg", ".inf", ".gadget", ".application", ".msc", ".chm", ".hlp",
    ".iso", ".img", ".vhd", ".vhdx", ".dmg", ".pkg", ".deb", ".rpm", ".appimage", ".run", ".elf", ".so",
    ".dylib", ".sh", ".bash", ".command", ".html", ".htm", ".xhtml", ".shtml", ".mht", ".mhtml", ".svgz",
    ".php", ".phtml", ".asp", ".aspx", ".jsp", ".docm", ".dotm", ".xlsm", ".xltm", ".xlam", ".pptm", ".potm",
    ".ppam", ".ppsm", ".sldm",
})
# In ZIP-Archiven erlaubt (Informatik-Projekte), oben aber gesperrt
ZIP_ALLOWED_EXTENSIONS = frozenset({".html", ".htm", ".xhtml", ".sh", ".bash", ".php", ".class", ".so"})

_EXEC_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\x7fELF", "Linux-Programme"),
    (b"\xfe\xed\xfa\xce", "macOS-Programme"), (b"\xfe\xed\xfa\xcf", "macOS-Programme"),
    (b"\xce\xfa\xed\xfe", "macOS-Programme"), (b"\xcf\xfa\xed\xfe", "macOS-Programme"),
    (b"\xca\xfe\xba\xbe", "Programmdateien (Mach-O/Java)"),
    (b"dex\n", "Android-Programme"),
    (b"\x00asm", "WebAssembly-Programme"),
    (b"L\x00\x00\x00\x01\x14\x02\x00", "Windows-Verknüpfungen"),
    (b"MSCF", "CAB-Archive"),
    (b"ITSF", "CHM-Hilfedateien"),
)
_HTML_MARKERS = (b"<!doctype html", b"<html", b"<head", b"<body", b"<script", b"<iframe", b"<frameset",
                 b"<object", b"<embed", b"<?php", b"<%@", b"<%=", b"<meta", b"<style", b"<link")
_TEXT_ACTIVE = (b"<script", b"javascript:", b"vbscript:", b"<iframe", b"<foreignobject", b"<embed", b"<object")
_EVENT_HANDLER_RE = re.compile(rb"[\s\"'/]on[a-z]{3,20}\s*=")
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_OLE_NAMES = frozenset({"WordDocument", "Workbook", "Book", "PowerPoint Document", "_VBA_PROJECT",
                        "_VBA_PROJECT_CUR", "VBA", "Macros", "\x01Ole10Native", "EncryptedPackage",
                        "EncryptionInfo"})
_HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1"}
_M4A_BRANDS = {b"M4A ", b"M4B ", b"M4P "}
_MOV_BRANDS = {b"qt  "}
_MP4_BRANDS = {b"isom", b"iso2", b"iso3", b"iso4", b"iso5", b"iso6", b"mp41", b"mp42", b"avc1", b"dash",
               b"M4V ", b"M4VH", b"M4VP", b"MSNV", b"mmp4", b"3gp4", b"3gp5", b"3gp6", b"3g2a", b"f4v ",
               b"XAVC", b"NDAS"}


def _blocked(reason: str) -> FileError:
    return FileError(415, "blocked_type", f"{reason} sind aus Sicherheitsgründen nicht erlaubt.")


def _unsupported(message: str | None = None) -> FileError:
    return FileError(415, "unsupported_type", message or "Dieser Dateityp ist nicht erlaubt. Erlaubt sind PDF, "
                     "EPUB, Bilder (PNG, JPEG, GIF, WebP, HEIC, TIFF), Office-/OpenDocument-Dateien, RTF, "
                     "Text/CSV/Markdown, gängige Audio-/Videoformate, GeoGebra, SMART Notebook, Scratch, H5P und "
                     "ZIP-Archive.")


# =========================================================================== Dateinamen
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
MAX_NAME_LENGTH = 180


def split_ext(name: str) -> tuple[str, str]:
    """``"bericht.final.pdf"`` → ``("bericht.final", ".pdf")``; Endungen nur aus 1–10 Buchstaben/Ziffern."""
    m = re.match(r"^(.+?)(\.[A-Za-z0-9]{1,10})$", name)
    return (m.group(1), m.group(2)) if m else (name, "")


def clean_filename(name: str | None) -> str:
    """Säubert einen Dateinamen: keine Pfade, Steuer-/Bidi-Zeichen, reservierten Zeichen/Namen; max. 180 Zeichen."""
    name = (name or "").replace("%22", '"').replace("%0D", "").replace("%0A", "")  # HTML-Formular-Kodierung
    name = unicodedata.normalize("NFC", name)
    name = re.split(r"[/\\]", name)[-1]
    out = []
    for ch in name:
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cf", "Cs", "Co", "Cn"):      # Steuer-, Format- (inkl. Bidi), Ersatz-, private Zeichen
            continue
        if ch in '<>:"|?*':
            out.append("_")
        elif cat.startswith("Z"):
            out.append(" ")
        else:
            out.append(ch)
    name = re.sub(r"\s+", " ", "".join(out)).strip(" .")
    stem, ext = split_ext(name)
    stem = stem.strip(" .")
    if stem.split(".")[0].upper() in _WINDOWS_RESERVED:
        stem = "_" + stem
    if not stem:
        stem = "datei"
    ext = ext.lower()
    if len(stem) + len(ext) > MAX_NAME_LENGTH:
        stem = stem[:MAX_NAME_LENGTH - len(ext)].rstrip(" .") or "datei"
    return stem + ext


def _final_name(clean: str, kind: FileKind) -> str:
    """Endung passend zum erkannten Inhalt (``foto`` → ``foto.jpg``, ``x.exe``(PDF) → ``x.pdf``)."""
    stem, ext = split_ext(clean)
    if ext in kind.extensions:
        return stem + ext
    if ext and (ext in KNOWN_EXTENSIONS or ext in BLOCKED_EXTENSIONS):
        base = stem
    else:
        base = clean
    base = base[:MAX_NAME_LENGTH - len(kind.extensions[0])].rstrip(" .") or "datei"
    return base + kind.extensions[0]


def content_disposition(filename: str, inline: bool = False) -> str:
    """``attachment; filename="ascii"; filename*=UTF-8''…`` (RFC 6266/5987, keine Header-Injektion)."""
    safe = clean_filename(filename)
    fallback = unicodedata.normalize("NFKD", safe).encode("ascii", "ignore").decode("ascii")
    fallback = re.sub(r"[^A-Za-z0-9._ ()+-]", "_", fallback).strip() or "datei"
    return f"{'inline' if inline else 'attachment'}; filename=\"{fallback}\"; filename*=UTF-8''{quote(safe, safe='')}"


# =========================================================================== Typerkennung
class _TailFile(io.RawIOBase):
    """Dateiersatz für ``zipfile``: kennt nur das Ende (``tail``) einer Datei der Länge ``size``."""

    def __init__(self, tail: bytes, size: int) -> None:
        super().__init__()
        self._tail = tail
        self._size = size
        self._start = size - len(tail)
        self._pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = 0) -> int:
        base = {0: 0, 1: self._pos, 2: self._size}[whence]
        pos = base + offset
        if pos < 0:
            raise OSError("ungültige Position")
        self._pos = pos
        return pos

    def tell(self) -> int:
        return self._pos

    def read(self, n: int = -1) -> bytes:
        if self._pos >= self._size:
            return b""
        if self._pos < self._start:
            raise OSError("Archivteil liegt außerhalb des geprüften Bereichs")
        rel = self._pos - self._start
        data = self._tail[rel:] if n is None or n < 0 else self._tail[rel:rel + n]
        self._pos += len(data)
        return data

    def readinto(self, b: Any) -> int:
        data = self.read(len(b))
        b[:len(data)] = data
        return len(data)


class Inspector:
    """Erkennt den Dateityp blockweise (Magic Bytes) und sammelt Hinweise auf aktive Inhalte."""

    PREFIX_MAX = 64 * 1024
    DECIDE_AT = 4096
    ZIP_TAIL_MAX = 4 * 1024 * 1024

    def __init__(self) -> None:
        self.prefix = bytearray()
        self.size = 0
        self.mode: str | None = None
        self.flags: set[str] = set()
        self.ole_names: set[str] = set()
        self._pending = bytearray()
        self._tail = bytearray()
        self._ole = bytearray()
        self._carry = b""

    # ------------------------------------------------------------------ Eingabe
    def feed(self, data: bytes) -> None:
        if not data:
            return
        self.size += len(data)
        if len(self.prefix) < self.PREFIX_MAX:
            self.prefix += data[:self.PREFIX_MAX - len(self.prefix)]
        if self.mode is None:
            self._pending += data
            if len(self._pending) < self.DECIDE_AT:
                return
            self._decide()
            return
        self._process(data)

    def finish(self) -> None:
        if self.mode is None:
            self._decide()

    def _decide(self) -> None:
        self.mode = _sniff_mode(bytes(self.prefix))
        pending, self._pending = bytes(self._pending), bytearray()
        self._process(pending)

    def _process(self, data: bytes) -> None:
        mode = self.mode
        if mode == "zip":
            self._tail += data
            if len(self._tail) > 2 * self.ZIP_TAIL_MAX:
                del self._tail[:len(self._tail) - self.ZIP_TAIL_MAX]
        elif mode == "ole":
            self._scan_ole(data)
        elif mode == "pdf":
            window = self._carry + data
            if b"/Launch" in window:
                self.flags.add("pdf_launch")
            self._carry = window[-16:]
        elif mode == "text":
            if b"\x00" in data:
                self.flags.add("nul")
            window = (self._carry + data).lower()
            if any(m in window for m in _TEXT_ACTIVE):
                self.flags.add("active")
            if _EVENT_HANDLER_RE.search(window):
                self.flags.add("event_handler")
            if b"\\object" in window or b"\\objdata" in window:
                self.flags.add("rtf_object")
            self._carry = window[-32:]

    def _scan_ole(self, data: bytes) -> None:
        """Verzeichniseinträge des Compound File (128-Byte-Raster) nach bekannten Stream-Namen durchsuchen."""
        buf = self._ole
        buf += data
        n = len(buf) - len(buf) % 128
        names = self.ole_names
        for pos in range(0, n, 128):
            name_len = buf[pos + 64] | (buf[pos + 65] << 8)
            if 2 <= name_len <= 64 and not name_len & 1 and buf[pos + 66] in (1, 2, 5):
                name = bytes(buf[pos:pos + name_len - 2]).decode("utf-16-le", "ignore")
                if name in _OLE_NAMES:
                    names.add(name)
        del buf[:n]

    # ------------------------------------------------------------------ ZIP
    def zip_entries(self) -> list[zipfile.ZipInfo]:
        tail = bytes(self._tail[-self.ZIP_TAIL_MAX:]) if len(self._tail) > self.ZIP_TAIL_MAX else bytes(self._tail)
        try:
            with zipfile.ZipFile(_TailFile(tail, self.size)) as zf:
                return zf.infolist()
        except (zipfile.BadZipFile, OSError, ValueError, KeyError, EOFError, NotImplementedError):
            raise _unsupported("Das ZIP-Archiv ist beschädigt oder zu umfangreich, um es zu prüfen.") from None


def _sniff_mode(p: bytes) -> str:
    if p.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "zip"
    if p.startswith(_OLE_MAGIC):
        return "ole"
    pdf_at = p[:1024].find(b"%PDF-")
    if pdf_at == 0 or (pdf_at > 0 and b"<" not in p[:pdf_at]):
        return "pdf"
    if _media_kind(p) is not None:
        return "media"
    return "text"


def _mp3_sync(p: bytes) -> bool:
    if len(p) < 4 or p[0] != 0xFF or (p[1] & 0xE0) != 0xE0:
        return False
    version, layer = (p[1] >> 3) & 3, (p[1] >> 1) & 3
    bitrate, rate = p[2] >> 4, (p[2] >> 2) & 3
    return version != 1 and layer != 0 and bitrate not in (0, 15) and rate != 3


def _ftyp_kind(p: bytes, ext: str = "") -> str | None:
    if p[4:8] != b"ftyp":
        return None
    box = int.from_bytes(p[0:4], "big")
    major = p[8:12]
    if major in (b"avif", b"avis", b"crx "):  # AVIF/Canon-RAW führen „mif1“ u. ä. als kompatible Marken
        return None
    brands = [major] + [p[i:i + 4] for i in range(16, min(len(p), max(16, box)), 4)]
    for brand in brands:
        if brand in _HEIC_BRANDS:
            return "heic"
        if brand in _M4A_BRANDS:
            return "m4a"
        if brand in _MOV_BRANDS:
            return "mov"
        if brand in _MP4_BRANDS:
            return "m4a" if ext == ".m4a" else "mp4"
    return None


def _media_kind(p: bytes, ext: str = "") -> str | None:
    if p.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if p.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if p[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if p[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if p[:4] == b"RIFF" and p[8:12] == b"WEBP":
        return "webp"
    if p[:4] == b"RIFF" and p[8:12] == b"WAVE":
        return "wav"
    if p[:4] == b"RIFF" and p[8:12] == b"AVI ":
        return "avi"
    kind = _ftyp_kind(p, ext)
    if kind:
        return kind
    if p[:4] == b"OggS":
        return "ogg"
    if p[:4] == b"fLaC":
        return "flac"
    if p[:4] == b"MThd":
        return "midi"
    if p[:4] == b"\x1aE\xdf\xa3":
        return "webm" if b"webm" in p[:4096] else "mkv" if b"matroska" in p[:4096] else None
    if p[:4] in (b"\x00\x00\x01\xba", b"\x00\x00\x01\xb3"):
        return "mpeg"
    if p[:3] == b"ID3" or _mp3_sync(p):
        return "mp3"
    if len(p) >= 7 and p[0] == 0xFF and (p[1] & 0xF6) == 0xF0:  # AAC (ADTS)
        return "aac"
    return None


def _is_text(p: bytes) -> bool:
    if p.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            codecs.getincrementaldecoder("utf-16")().decode(p[:len(p) - len(p) % 2], final=False)
            return True
        except UnicodeDecodeError:
            return False
    try:
        codecs.getincrementaldecoder("utf-8")().decode(p, final=False)
        return True
    except UnicodeDecodeError:
        pass
    # Windows-1252/Latin-1: keine Steuerzeichen außer Tab/Zeilenumbrüchen/Seitenvorschub
    return not any(b < 0x20 and b not in (9, 10, 12, 13, 26) for b in p)


def _odf_mimetype(p: bytes) -> str | None:
    """ODF: erster Eintrag ``mimetype`` (unkomprimiert) enthält den Typ."""
    if len(p) < 38 or p[:4] != b"PK\x03\x04":
        return None
    method = int.from_bytes(p[8:10], "little")
    csize = int.from_bytes(p[18:22], "little")
    name_len = int.from_bytes(p[26:28], "little")
    extra_len = int.from_bytes(p[28:30], "little")
    if p[30:30 + name_len] != b"mimetype" or method != 0 or not 0 < csize < 200:
        return None
    start = 30 + name_len + extra_len
    try:
        return p[start:start + csize].decode("ascii")
    except UnicodeDecodeError:
        return None


def _classify_zip(insp: Inspector, ext: str) -> FileKind:
    infos = insp.zip_entries()
    names = [i.filename for i in infos]
    lower = [n.lower().replace("\\", "/") for n in names]
    if any(i.flag_bits & 0x1 for i in infos):
        raise _blocked("Verschlüsselte (passwortgeschützte) Archive – sie lassen sich nicht prüfen –")
    if any(n.startswith("/") or ".." in n.split("/") or re.match(r"^[a-z]:", n) for n in lower):
        raise _blocked("Archive mit ungültigen Pfaden")
    if "meta-inf/manifest.mf" in lower and any(n.endswith(".class") for n in lower):
        raise _blocked("Java-Programme (JAR)")
    if "androidmanifest.xml" in lower or "classes.dex" in lower:
        raise _blocked("Android-Apps (APK)")
    if any(n.startswith("payload/") and ".app/" in n for n in lower):
        raise _blocked("iOS-Apps (IPA)")

    def no_programs(extra: frozenset[str] = frozenset()) -> None:
        for n in lower:
            suffix = split_ext(n.rsplit("/", 1)[-1])[1]
            if suffix in BLOCKED_EXTENSIONS and suffix not in ZIP_ALLOWED_EXTENSIONS and suffix not in extra:
                raise _blocked("Archive mit ausführbaren Dateien oder Makro-Dokumenten")

    container = _CONTAINERS.get(ext)
    if container and container[1] in lower:   # GeoGebra, SMART Notebook, Scratch, H5P: Endung bleibt erhalten
        no_programs(_CONTAINER_ALLOWED)
        return KINDS[container[0]]
    odf = _odf_mimetype(bytes(insp.prefix))
    if odf == "application/epub+zip":
        no_programs(_CONTAINER_ALLOWED)
        return KINDS["epub"]
    if odf:
        if any(n.startswith(("basic/", "scripts/")) for n in lower):
            raise _blocked("OpenDocument-Dateien mit Makros")
        key = {"application/vnd.oasis.opendocument.text": "odt",
               "application/vnd.oasis.opendocument.text-template": "odt",
               "application/vnd.oasis.opendocument.spreadsheet": "ods",
               "application/vnd.oasis.opendocument.spreadsheet-template": "ods",
               "application/vnd.oasis.opendocument.presentation": "odp",
               "application/vnd.oasis.opendocument.presentation-template": "odp",
               "application/vnd.oasis.opendocument.graphics": "odg",
               "application/vnd.oasis.opendocument.graphics-template": "odg"}.get(odf)
        if key:
            return KINDS[key]
        if ext != ".zip":
            raise _unsupported("Dieser OpenDocument-Typ ist nicht erlaubt (erlaubt: Text, Tabelle, Präsentation, "
                               "Zeichnung).")
    if "[content_types].xml" in lower:
        if any(n.endswith("vbaproject.bin") or "/activex/" in n or n.endswith("vbadata.xml") for n in lower):
            raise _blocked("Office-Dateien mit Makros oder ActiveX")
        for prefix, key in (("word/", "docx"), ("xl/", "xlsx"), ("ppt/", "pptx")):
            if any(n.startswith(prefix) for n in lower):
                return KINDS[key]
    no_programs()
    return KINDS["zip"]


def _classify_ole(insp: Inspector, ext: str) -> FileKind:
    names = insp.ole_names
    if names & {"EncryptedPackage", "EncryptionInfo"}:
        raise _blocked("Passwortgeschützte Office-Dateien – sie lassen sich nicht prüfen –")
    if names & {"_VBA_PROJECT", "_VBA_PROJECT_CUR", "VBA", "Macros"}:
        raise _blocked("Office-Dateien mit Makros")
    if "\x01Ole10Native" in names:
        raise _blocked("Office-Dateien mit eingebetteten Programmen (OLE-Pakete)")
    found = [key for key, stream in (("doc", {"WordDocument"}), ("xls", {"Workbook", "Book"}),
                                     ("ppt", {"PowerPoint Document"})) if names & stream]
    wanted = {".doc": "doc", ".xls": "xls", ".ppt": "ppt"}.get(ext)
    if wanted and wanted in found:
        return KINDS[wanted]
    if found:
        return KINDS[found[0]]
    raise _unsupported("Dieses Office-/OLE-Format ist nicht erlaubt (z. B. MSI-Installer, Outlook-Nachrichten).")


def classify(insp: Inspector, filename: str, declared_type: str | None = None, *,
             extra: Iterable[str] = ()) -> FileKind:
    """Ermittelt die Dateiart; :class:`FileError` 415 bei nicht erlaubten/aktiven Inhalten, 422 bei leerer Datei.

    ``extra`` = freigeschaltete Zusatzarten des Zwecks (``code``: Quelltext wie ``.py``/``.java``/``.js``/``.html``,
    gespeichert als ``text/plain`` und nur als Download ausgeliefert)."""
    insp.finish()
    extra = frozenset(extra)
    ext = split_ext(filename)[1].lower()
    p = bytes(insp.prefix)
    if insp.size == 0:
        raise FileError(422, "empty_file", "Die Datei ist leer.")
    if p.startswith(b"MZ") and b"\x00" in p[:64]:
        raise _blocked("Windows-Programme")
    for magic, label in _EXEC_MAGIC:
        if p.startswith(magic):
            raise _blocked(label)
    if insp.mode == "zip":
        return _classify_zip(insp, ext)
    if insp.mode == "ole":
        return _classify_ole(insp, ext)
    if insp.mode == "pdf":
        if "pdf_launch" in insp.flags:
            raise _blocked("PDF-Dateien mit Startbefehlen (/Launch)")
        return KINDS["pdf"]
    media = _media_kind(p, ext)
    if media:
        return KINDS[media]
    # Textartige Inhalte
    head = p.lstrip(b"\xef\xbb\xbf \t\r\n")[:1024].lower()
    textual = insp.mode == "text" and _is_text(p) and ("nul" not in insp.flags or p.startswith((b"\xff\xfe", b"\xfe\xff")))
    if "code" in extra and ext in CODE_EXTENSIONS and textual:
        return KINDS["code"]
    if head.startswith(b"{\\rtf") and textual:
        if "rtf_object" in insp.flags:
            raise _blocked("RTF-Dokumente mit eingebetteten Objekten")
        return KINDS["rtf"]
    if head.startswith(b"#!"):
        raise _blocked("Skripte")
    if head.startswith(b"<svg") or (head.startswith((b"<?xml", b"<!--", b"<!doctype svg"))
                                    and b"<svg" in p[:8192].lower()):
        if insp.flags & {"active", "event_handler"}:
            raise _blocked("SVG-Grafiken mit Skripten")
        return KINDS["svg"]
    if any(head.startswith(m) for m in _HTML_MARKERS):
        raise _blocked("HTML-Seiten und Skripte")
    if head.startswith(b"<?xml"):
        raise _unsupported("XML-Dateien sind nicht erlaubt.")
    if textual:
        if ext in BLOCKED_EXTENSIONS:
            raise _blocked("Skripte und ausführbare Dateien")
        for key in ("txt", "csv", "md"):
            if ext in KINDS[key].extensions:
                return KINDS[key]
        if not ext:
            declared = (declared_type or "").split(";")[0].strip().lower()
            return KINDS["csv"] if declared == "text/csv" else KINDS["md"] if declared == "text/markdown" \
                else KINDS["txt"]
        raise _unsupported("Textdateien sind nur als .txt, .csv, .md, .tex, .srt oder .vtt erlaubt"
                           + (" (Quelltext nur in Kursräumen)." if ext in CODE_EXTENSIONS else "."))
    if ext in BLOCKED_EXTENSIONS:
        raise _blocked("Ausführbare Dateien")
    raise _unsupported()


# =========================================================================== Virenscan (ClamAV, optional)
class ClamAVStream:
    """``INSTREAM``-Prüfung über clamd (TCP). Fehler werden gesammelt, nicht geworfen."""

    PIECE = 1024 * 1024

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host, self.port, self.timeout = host, port, timeout
        self.sock: socket.socket | None = None
        self.error: str | None = None

    def _connect(self) -> None:
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self.sock.sendall(b"zINSTREAM\0")
        except OSError as exc:
            self.error = f"clamd nicht erreichbar ({exc.__class__.__name__})"
            self.close()

    def send(self, data: bytes) -> None:
        if self.error:
            return
        if self.sock is None:
            self._connect()
            if self.error:
                return
        try:
            for i in range(0, len(data), self.PIECE):
                piece = data[i:i + self.PIECE]
                self.sock.sendall(struct.pack(">I", len(piece)) + piece)  # type: ignore[union-attr]
        except OSError as exc:
            self.error = f"Übertragung an clamd abgebrochen ({exc.__class__.__name__})"
            self.close()

    def finish(self) -> tuple[str, str | None]:
        """→ ``("clean", None)``, ``("virus", signatur)`` oder ``("error", grund)``."""
        if self.sock is None and not self.error:
            self._connect()
        if self.error or self.sock is None:
            return "error", self.error or "clamd nicht erreichbar"
        try:
            self.sock.sendall(b"\0\0\0\0")
            reply = b""
            while not reply.endswith(b"\0") and len(reply) < 4096:
                part = self.sock.recv(4096)
                if not part:
                    break
                reply += part
        except OSError as exc:
            return "error", f"keine Antwort von clamd ({exc.__class__.__name__})"
        finally:
            self.close()
        text = reply.rstrip(b"\0").decode("utf-8", "replace").strip()
        if text.endswith(" OK") or text == "stream: OK":
            return "clean", None
        if text.endswith(" FOUND"):
            return "virus", text.split(":", 1)[-1].rsplit(" FOUND", 1)[0].strip()[:200]
        return "error", text[:200] or "leere Antwort von clamd"

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


# =========================================================================== Ablage (Pfade, Temp-Dateien)
def files_root() -> Path:
    return Path(config.files_dir)


def _check_id(file_id: str) -> str:
    if not isinstance(file_id, str) or not ID_RE.match(file_id):
        raise _not_found()
    return file_id


def blob_path(file_id: str) -> Path:
    """Pfad des verschlüsselten Inhalts (ID wird streng geprüft → kein Path-Traversal)."""
    _check_id(file_id)
    return files_root() / file_id[:2] / file_id[2:4] / file_id


def _tmp_dir() -> Path:
    path = files_root() / "tmp"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


class UploadSink:
    """Nimmt Klartext-Blöcke an: Limit, SHA-256, Typerkennung, Virenscan, Verschlüsselung → Temp-Datei."""

    def __init__(self, max_bytes: int, file_id: str | None = None) -> None:
        self.id = file_id or str(uuid.uuid4())
        self.max_bytes = max_bytes
        self.size = 0
        self.sha256 = ""
        self.scan: tuple[str, str | None] = ("unscanned", None)
        self.inspector = Inspector()
        self.tmp_path = _tmp_dir() / f"{self.id}.tmp"
        fd = os.open(self.tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self._fh: io.BufferedWriter | None = os.fdopen(fd, "wb")
        self._enc = crypto.StreamEncryptor(aad=self.id.encode("ascii"))
        self.key_id = self._enc.key_id
        self._fh.write(self._enc.header)
        self._sha = hashlib.sha256()
        self._scanner = ClamAVStream(config.clamav_host, config.clamav_port, config.clamav_timeout) \
            if config.clamav_host else None

    def write(self, data: bytes) -> None:
        if not data:
            return
        self.size += len(data)
        if self.size > self.max_bytes:
            raise FileError(413, "file_too_large", f"Die Datei ist zu groß (höchstens {_mb(self.max_bytes)}).",
                            max_bytes=self.max_bytes)
        self._sha.update(data)
        self.inspector.feed(data)
        if self._scanner is not None:
            self._scanner.send(data)
        assert self._fh is not None
        self._fh.write(self._enc.update(data))

    def write_many(self, pieces: Iterable[bytes]) -> None:
        for piece in pieces:
            self.write(piece)

    def finish(self) -> None:
        assert self._fh is not None
        self._fh.write(self._enc.finalize())
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._fh.close()
        self._fh = None
        self.sha256 = self._sha.hexdigest()
        self.inspector.finish()
        if self._scanner is not None:
            self.scan = self._scanner.finish()

    def discard(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            except OSError:
                pass
            self._fh = None
        if self._scanner is not None:
            self._scanner.close()
        self.tmp_path.unlink(missing_ok=True)


# =========================================================================== Zwecke, Quoten, Zugriff
@dataclass(frozen=True)
class Purpose:
    name: str
    kinds: frozenset[str] | None = None     # erlaubte Arten (None = ganze Allowlist)
    max_bytes: int | None = None            # strengeres Limit als SM_UPLOAD_MAX_MB
    extra: frozenset[str] = frozenset()     # zusätzlich freigeschaltete Arten (OPT_IN_KINDS, z. B. „code“)


_purposes: dict[str, Purpose] = {}
AccessCheck = Callable[[Session, Any, StoredFile], bool]
_access_checks: dict[str, AccessCheck] = {}


def _expand_kinds(kinds: Iterable[str]) -> set[str]:
    expanded: set[str] = set()
    for k in kinds:
        if k in KINDS:
            expanded.add(k)
        elif k in GROUPS:
            expanded |= GROUPS[k]
        else:
            raise ValueError(f"Unbekannte Dateiart {k!r}")
    return expanded


def register_purpose(name: str, kinds: Iterable[str] | None = None, max_mb: float | None = None, *,
                     extra_kinds: Iterable[str] | None = None) -> None:
    """Optionale Regeln je Zweck, z. B. ``register_purpose("student_document", kinds=["pdf", "image"], max_mb=10)``.

    ``kinds`` = Schlüssel aus :data:`KINDS` und/oder Gruppen (``image``, ``office``, ``text``, ``audio``, ``video``,
    ``archive``, ``document``, ``app``). Nicht registrierte Zwecke nutzen die allgemeine Allowlist (ohne
    :data:`OPT_IN_KINDS`). ``extra_kinds`` schaltet Zusatzarten frei, z. B. ``["code"]`` (Quelltext, nur Download).
    """
    if not PURPOSE_RE.match(name):
        raise ValueError(f"Ungültiger Zweck {name!r}")
    expanded = _expand_kinds(kinds or ())
    extra = _expand_kinds(extra_kinds or ()) & OPT_IN_KINDS
    _purposes[name] = Purpose(name, frozenset(expanded | extra) if kinds is not None else None,
                              int(max_mb * 1024 * 1024) if max_mb else None, frozenset(extra))


def purpose_rules(name: str) -> Purpose:
    return _purposes.get(name) or Purpose(name)


def register_access_check(ref_type: str, fn: AccessCheck) -> None:
    """Zugriffsprüfung für angehängte Dateien: ``fn(db, user, stored_file) -> bool`` (``user`` = ``AuthUser``).

    Wird für jeden Download/Metadatenabruf eines Nicht-Eigentümers aufgerufen; ohne registrierte Prüfung hat nur
    der Eigentümer Zugriff. Ausnahmen in ``fn`` gelten als „kein Zugriff“.
    """
    if not REF_TYPE_RE.match(ref_type) or not callable(fn):
        raise ValueError("register_access_check(ref_type, fn) braucht einen gültigen ref_type und eine Funktion")
    _access_checks[ref_type] = fn


def max_upload_bytes(purpose: str | None = None) -> int:
    limit = int(config.upload_max_mb * 1024 * 1024)
    rules = purpose_rules(purpose) if purpose else None
    if rules and rules.max_bytes:
        limit = min(limit, rules.max_bytes)
    return limit


def _is_real_user(user: Any) -> bool:
    return user is not None and bool(getattr(user, "id", 0))


def quota_bytes(user: Any) -> int | None:
    """Speicherkontingent des Kontos (``None`` = unbegrenzt; 0 MB in der Konfiguration = unbegrenzt)."""
    from .permissions import STAFF_ROLES

    mb = config.quota_mb_staff if getattr(user, "role", "") in STAFF_ROLES else config.quota_mb_student
    return int(mb * 1024 * 1024) if mb > 0 else None


def usage_bytes(db: Session, user_id: int) -> int:
    return int(db.scalar(select(func.coalesce(func.sum(StoredFile.size), 0))
                         .where(StoredFile.owner_user_id == user_id, StoredFile.deleted_at.is_(None))) or 0)


def _check_quota(db: Session, user: Any, extra: int) -> None:
    if not _is_real_user(user):
        return
    quota = quota_bytes(user)
    if quota is None:
        return
    used = usage_bytes(db, user.id)
    if used + extra > quota:
        raise FileError(413, "quota_exceeded", f"Ihr Speicherplatz reicht nicht: {_mb(used)} von {_mb(quota)} belegt. "
                        "Bitte nicht mehr benötigte Dateien löschen.", used_bytes=used, quota_bytes=quota)


def get_file(db: Session, file_id: str, *, include_deleted: bool = False) -> StoredFile | None:
    if not isinstance(file_id, str) or not ID_RE.match(file_id):
        return None
    meta = db.get(StoredFile, file_id)
    if meta is None or (meta.deleted_at is not None and not include_deleted):
        return None
    return meta


def can_read(db: Session, user: Any, meta: StoredFile) -> bool:
    """Eigentümer immer; sonst nur die registrierte Prüfung des ``ref_type`` (kein Admin-Generalschlüssel)."""
    if meta is None or meta.deleted_at is not None or not _is_real_user(user):
        return False
    if meta.owner_user_id is not None and meta.owner_user_id == user.id:
        return True
    check = _access_checks.get(meta.ref_type or "")
    if check is None:
        return False
    try:
        return bool(check(db, user, meta))
    except Exception:  # noqa: BLE001 - fehlerhafte Prüfungen verweigern den Zugriff
        log.exception("Zugriffsprüfung für ref_type %s fehlgeschlagen", meta.ref_type)
        return False


def require_readable(db: Session, user: Any, file_id: str) -> StoredFile:
    """Metadaten einer lesbaren Datei, sonst 404 (Existenz fremder Dateien wird nicht verraten)."""
    meta = get_file(db, file_id)
    if meta is None or not can_read(db, user, meta):
        raise _not_found()
    return meta


def file_info(meta: StoredFile, user: Any = None) -> dict[str, Any]:
    """JSON-Darstellung (für Listen; Frontend-Typ ``StoredFileInfo``)."""
    kind = KINDS.get(meta.kind)
    owner = _is_real_user(user) and meta.owner_user_id == user.id
    return {"id": meta.id, "filename": meta.filename, "size": meta.size, "content_type": meta.content_type,
            "kind": meta.kind, "kind_label": kind.label if kind else meta.kind, "group": kind.group if kind else "",
            "inline": bool(kind and kind.inline), "purpose": meta.purpose, "attached": meta.attached,
            "ref_type": meta.ref_type, "ref_id": meta.ref_id, "created_at": iso(meta.created_at),
            "scan_status": meta.scan_status, "owner": owner,
            "can_delete": owner and not meta.attached, "url": f"/api/v1/files/{meta.id}"}


def files_info(db: Session, file_ids: Iterable[str], user: Any = None, *, check_access: bool = True
               ) -> list[dict[str, Any]]:
    """Mehrere Dateien (z. B. Anhänge) in gegebener Reihenfolge; fehlende/unlesbare werden ausgelassen."""
    ids = [i for i in dict.fromkeys(file_ids) if isinstance(i, str) and ID_RE.match(i)]
    if not ids:
        return []
    rows = {m.id: m for m in db.scalars(select(StoredFile).where(StoredFile.id.in_(ids),
                                                                 StoredFile.deleted_at.is_(None)))}
    return [file_info(rows[i], user) for i in ids
            if i in rows and (not check_access or can_read(db, user, rows[i]))]


# =========================================================================== Speichern
def _ref_value(value: Any) -> str:
    text = str(value)
    if not text or len(text) > 80:
        raise ValueError("ref_id muss 1–80 Zeichen lang sein")
    return text


def _finalize(db: Session, user: Any, sink: UploadSink, filename: str | None, declared_type: str | None,
              purpose: str) -> StoredFile:
    """Prüft das Ergebnis eines Uploads und legt Metadaten + verschlüsselten Inhalt endgültig ab (ohne Commit)."""
    from .audit import audit_now

    rules = purpose_rules(purpose)
    clean = clean_filename(filename)
    try:
        kind = classify(sink.inspector, clean, declared_type, extra=rules.extra)
    except FileError as exc:
        if exc.code == "blocked_type":
            log.warning("Upload blockiert (%s, %d Byte, Zweck %s)", exc.message, sink.size, purpose)
            audit_now(user if _is_real_user(user) else None, "file.blocked", f"file:{sink.id}",
                      {"reason": exc.message, "size": sink.size, "purpose": purpose})
        raise
    if rules.kinds is not None and kind.key not in rules.kinds:
        allowed = ", ".join(sorted({KINDS[k].label for k in rules.kinds}))
        raise FileError(415, "unsupported_type", f"Für diesen Zweck sind nur folgende Dateiarten erlaubt: {allowed}.")
    if rules.max_bytes and sink.size > rules.max_bytes:
        raise FileError(413, "file_too_large", f"Die Datei ist zu groß (höchstens {_mb(rules.max_bytes)}).",
                        max_bytes=rules.max_bytes)
    status, detail = sink.scan
    if status == "virus":
        log.warning("Virenscanner: Schadsoftware erkannt (%s), Upload abgelehnt", detail)
        audit_now(user if _is_real_user(user) else None, "file.virus", f"file:{sink.id}",
                  {"signature": detail, "size": sink.size, "purpose": purpose})
        raise FileError(422, "virus_found", "Die Datei wurde vom Virenscanner als gefährlich erkannt und abgelehnt.")
    if status == "error":
        if config.clamav_required:
            log.error("Virenscan fehlgeschlagen (%s) – Upload abgelehnt (SM_CLAMAV_REQUIRED=1)", detail)
            raise FileError(503, "scan_failed", "Der Virenscanner ist gerade nicht erreichbar. Bitte später erneut "
                            "versuchen.")
        log.warning("Virenscan fehlgeschlagen (%s) – Datei wird ungeprüft angenommen", detail)
    _check_quota(db, user, sink.size)
    now = utcnow()
    meta = StoredFile(id=sink.id, owner_user_id=user.id if _is_real_user(user) else None,
                      content_type=kind.mime, kind=kind.key, size=sink.size, sha256=sink.sha256, purpose=purpose,
                      key_id=sink.key_id, scan_status=status, created_at=now)
    meta.filename = _final_name(clean, kind)
    db.add(meta)
    db.flush()
    target = blob_path(sink.id)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.replace(sink.tmp_path, target)
    return meta


def _check_purpose(purpose: str | None) -> str:
    purpose = (purpose or DEFAULT_PURPOSE).strip().lower()
    if not PURPOSE_RE.match(purpose):
        raise FileError(422, "invalid_purpose", "Ungültiger Zweck (purpose): 2–40 Zeichen a–z, 0–9, _ . -")
    return purpose


def store_bytes(db: Session, user: Any, data: bytes, filename: str, content_type: str | None = None,
                purpose: str = DEFAULT_PURPOSE) -> StoredFile:
    """Speichert Daten verschlüsselt (gleiche Prüfungen wie der HTTP-Upload; ``user=None`` = System, ohne Quote).

    Gibt das neue :class:`StoredFile` zurück (``flush``, Commit macht der Aufrufer). Fehler: :class:`FileError`.
    """
    purpose = _check_purpose(purpose)
    _check_quota(db, user, 0)
    sink = UploadSink(max_upload_bytes(purpose))
    try:
        view = memoryview(bytes(data))
        for i in range(0, len(view), 1024 * 1024):
            sink.write(bytes(view[i:i + 1024 * 1024]))
        sink.finish()
        return _finalize(db, user, sink, filename, content_type, purpose)
    finally:
        sink.discard()


async def store_upload(request: Any, db: Session, user: Any) -> StoredFile:
    """Streamt einen ``multipart/form-data``-Upload (Feld ``file``, optional ``purpose`` bzw. ``?purpose=``).

    Das Größenlimit greift schon während der Übertragung; Klartext wird nie zwischengespeichert. Ohne Commit.
    """
    from starlette.concurrency import run_in_threadpool

    try:
        from python_multipart.exceptions import FormParserError
        from python_multipart.multipart import MultipartParser, parse_options_header
    except ModuleNotFoundError:  # python-multipart < 0.0.13 (alter Importname)
        from multipart.exceptions import FormParserError  # type: ignore[no-redef]
        from multipart.multipart import MultipartParser, parse_options_header  # type: ignore[no-redef]

    mime, params = parse_options_header(request.headers.get("content-type", ""))
    if mime != b"multipart/form-data" or b"boundary" not in params:
        raise FileError(400, "bad_request", "Erwartet wird multipart/form-data mit dem Feld 'file'.")
    query_purpose = request.query_params.get("purpose")
    purpose = _check_purpose(query_purpose) if query_purpose else None
    limit = max_upload_bytes(purpose)
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > limit + FORM_OVERHEAD:
        raise FileError(413, "file_too_large", f"Die Datei ist zu groß (höchstens {_mb(limit)}).", max_bytes=limit)
    await run_in_threadpool(_check_quota, db, user, 0)

    state: dict[str, Any] = {"headers": [], "name": b"", "value": b"", "file": None, "field": None,
                             "fields": {}, "file_seen": False, "pending": []}

    def on_part_begin() -> None:
        state["headers"], state["field"] = [], None

    def on_header_field(data: bytes, start: int, end: int) -> None:
        state["name"] += data[start:end]

    def on_header_value(data: bytes, start: int, end: int) -> None:
        state["value"] += data[start:end]

    def on_header_end() -> None:
        state["headers"].append((state["name"].lower(), state["value"]))
        state["name"], state["value"] = b"", b""

    def on_headers_finished() -> None:
        disp = next((v for k, v in state["headers"] if k == b"content-disposition"), b"")
        ctype = next((v for k, v in state["headers"] if k == b"content-type"), b"")
        _, opts = parse_options_header(disp)
        name = opts.get(b"name", b"")
        if b"filename" in opts:
            if state["file_seen"]:
                raise FileError(400, "bad_request", "Bitte nur eine Datei je Upload senden.")
            if name != b"file":
                raise FileError(400, "bad_request", "Die Datei muss im Feld 'file' gesendet werden.")
            raw = opts[b"filename"]
            try:
                fname = raw.decode("utf-8")
            except UnicodeDecodeError:
                fname = raw.decode("latin-1")
            state["file_seen"] = True
            state["file"] = {"filename": fname, "content_type": ctype.decode("latin-1")}
            state["field"] = None
        else:
            state["field"] = [name.decode("latin-1"), bytearray()]

    def on_part_data(data: bytes, start: int, end: int) -> None:
        field = state["field"]
        if field is not None:
            field[1] += data[start:end]
            if len(field[1]) > 256:
                raise FileError(400, "bad_request", "Formularfeld zu lang.")
        else:
            state["pending"].append(bytes(data[start:end]))

    def on_part_end() -> None:
        field = state["field"]
        if field is not None:
            if len(state["fields"]) > 10:
                raise FileError(400, "bad_request", "Zu viele Formularfelder.")
            state["fields"][field[0]] = bytes(field[1]).decode("utf-8", "replace")
            state["field"] = None

    parser = MultipartParser(params[b"boundary"], {
        "on_part_begin": on_part_begin, "on_header_field": on_header_field, "on_header_value": on_header_value,
        "on_header_end": on_header_end, "on_headers_finished": on_headers_finished, "on_part_data": on_part_data,
        "on_part_end": on_part_end})
    sink: UploadSink | None = None
    received = 0
    try:
        async for chunk in request.stream():
            received += len(chunk)
            if received > limit + FORM_OVERHEAD:
                raise FileError(413, "file_too_large", f"Die Datei ist zu groß (höchstens {_mb(limit)}).",
                                max_bytes=limit)
            try:
                parser.write(chunk)
            except FormParserError:
                raise FileError(400, "bad_request", "Fehlerhafte Multipart-Daten.") from None
            if state["pending"]:
                if purpose is None and "purpose" in state["fields"]:
                    purpose = _check_purpose(state["fields"]["purpose"])
                    limit = max_upload_bytes(purpose)
                if sink is None:
                    sink = await run_in_threadpool(UploadSink, limit)
                pieces, state["pending"] = state["pending"], []
                await run_in_threadpool(sink.write_many, pieces)
        try:
            parser.finalize()
        except FormParserError:
            raise FileError(400, "bad_request", "Fehlerhafte Multipart-Daten.") from None
        if not state["file_seen"]:
            raise FileError(422, "no_file", "Es wurde keine Datei übermittelt (Feld 'file').")
        if purpose is None:
            purpose = _check_purpose(state["fields"].get("purpose"))
        if sink is None:  # leere Datei
            sink = await run_in_threadpool(UploadSink, limit)
        if state["pending"]:
            pieces, state["pending"] = state["pending"], []
            await run_in_threadpool(sink.write_many, pieces)
        await run_in_threadpool(sink.finish)
        info = state["file"] or {}
        return await run_in_threadpool(_finalize, db, user, sink, info.get("filename"), info.get("content_type"),
                                       purpose)
    finally:
        if sink is not None:
            await run_in_threadpool(sink.discard)


# =========================================================================== Lesen & Ausliefern
def iter_plaintext(meta: StoredFile, read_size: int = 256 * 1024) -> Iterator[bytes]:
    """Entschlüsselt den Inhalt blockweise (Generator). Fehlender/beschädigter Inhalt → :class:`FileError`."""
    path = blob_path(meta.id)
    try:
        fh = open(path, "rb")
    except FileNotFoundError:
        log.error("Inhalt der Datei %s fehlt im Speicher (%s)", meta.id, path)
        raise FileError(404, "blob_missing", "Der Dateiinhalt ist nicht mehr vorhanden.") from None
    with fh:
        try:
            yield from crypto.decrypt_stream(fh, meta.id.encode("ascii"), read_size)
        except crypto.CryptoError as exc:
            log.error("Datei %s lässt sich nicht entschlüsseln: %s", meta.id, exc)
            raise FileError(500, "decrypt_failed", "Die Datei ist beschädigt oder der Schlüssel fehlt.") from None


def read_bytes(meta: StoredFile) -> bytes:
    data = b"".join(iter_plaintext(meta))
    if hashlib.sha256(data).hexdigest() != meta.sha256:
        log.error("Prüfsumme der Datei %s stimmt nicht", meta.id)
        raise FileError(500, "decrypt_failed", "Die Datei ist beschädigt (Prüfsumme).")
    return data


def read_file(db: Session, file_id: str) -> tuple[StoredFile, bytes]:
    """Metadaten + Klartext (ohne Rechteprüfung – vorher :func:`can_read`/:func:`require_readable`!)."""
    meta = get_file(db, file_id)
    if meta is None:
        raise _not_found()
    return meta, read_bytes(meta)


def _inline_allowed(meta: StoredFile, inline: bool) -> bool:
    kind = KINDS.get(meta.kind)
    return bool(inline and kind and kind.inline)


def download_headers(meta: StoredFile, inline: bool = False) -> dict[str, str]:
    """Sichere Header: ``filename*``, ``nosniff``, CSP ``sandbox`` (PDF inline: ohne sandbox, da sonst die
    eingebauten PDF-Betrachter blockiert werden – der Typ ist per ``nosniff`` festgenagelt), keine Zwischenspeicherung."""
    inline = _inline_allowed(meta, inline)
    if inline and meta.kind == "pdf":
        csp = "default-src 'none'; object-src 'self'; img-src 'self' data: blob:; style-src 'unsafe-inline'; " \
              "frame-ancestors 'self'"
    else:
        csp = "sandbox; default-src 'none'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'; " \
              "frame-ancestors 'self'"
    return {
        "Content-Disposition": content_disposition(meta.filename, inline),
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": csp,
        "Cross-Origin-Resource-Policy": "same-origin",
        "X-Frame-Options": "SAMEORIGIN",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "private, no-store",
    }


def file_response(meta: StoredFile, data: bytes, inline: bool = False) -> Response:
    """Antwort mit sicheren Download-Headern (aktive Inhalte wie SVG nie inline)."""
    return Response(content=data, media_type=meta.content_type, headers=download_headers(meta, inline))


def stream_response(meta: StoredFile, inline: bool = False) -> Response:
    """Wie :func:`file_response`, aber kleine Dateien vollständig geprüft und große gestreamt (konstanter Speicher)."""
    if meta.size <= SMALL_FILE_BYTES:
        return file_response(meta, read_bytes(meta), inline)
    iterator = iter_plaintext(meta)
    first = next(iterator, b"")  # Kopf + erster Block geprüft, bevor die Antwort beginnt

    def body() -> Iterator[bytes]:
        if first:
            yield first
        yield from iterator

    headers = download_headers(meta, inline)
    headers["Content-Length"] = str(meta.size)
    return StreamingResponse(body(), media_type=meta.content_type, headers=headers)


_audit_seen: OrderedDict[tuple[int, str, str], None] = OrderedDict()
_audit_lock = threading.Lock()


def audit_download(db: Session, user: Any, meta: StoredFile, ip: str | None = None) -> bool:
    """Protokolliert den Abruf einer fremden Datei (höchstens einmal je Konto, Datei und Tag). Ohne Commit."""
    from .audit import audit

    if not _is_real_user(user) or meta.owner_user_id == user.id:
        return False
    key = (int(user.id), meta.id, utcnow().date().isoformat())
    with _audit_lock:
        if key in _audit_seen:
            _audit_seen.move_to_end(key)
            return False
        _audit_seen[key] = None
        while len(_audit_seen) > 50_000:
            _audit_seen.popitem(last=False)
    audit(db, user, "file.download", f"file:{meta.id}",
          {"ref_type": meta.ref_type, "ref_id": meta.ref_id, "purpose": meta.purpose, "owner": meta.owner_user_id},
          ip=ip)
    return True


# =========================================================================== Anhängen, Lösen, Löschen
def attach(db: Session, file_id: str, user: Any, ref_type: str, ref_id: Any, *,
           kinds: Iterable[str] | None = None) -> StoredFile:
    """Bindet eine eigene, noch nicht angehängte Datei an ein Objekt (``ref_type``/``ref_id``). Ohne Commit.

    ``user=None`` (System) darf jede nicht angehängte Datei binden. ``kinds`` prüft zusätzlich die Dateiart
    (Schlüssel/Gruppen wie bei :func:`register_purpose`). Fehler: 404 fremd/unbekannt, 409 schon angehängt, 415 Art.
    """
    if not REF_TYPE_RE.match(ref_type or ""):
        raise ValueError(f"Ungültiger ref_type {ref_type!r}")
    meta = get_file(db, file_id)
    if meta is None or (_is_real_user(user) and meta.owner_user_id != user.id):
        raise _not_found()
    if meta.ref_type:
        if meta.ref_type == ref_type and meta.ref_id == str(ref_id):
            return meta
        raise FileError(409, "already_attached", "Die Datei ist bereits an anderer Stelle angehängt.")
    if kinds is not None:
        allowed: set[str] = set()
        for k in kinds:
            allowed |= GROUPS.get(k, frozenset({k}))
        if meta.kind not in allowed:
            raise FileError(415, "unsupported_type", "Diese Dateiart ist hier nicht erlaubt.")
    meta.ref_type = ref_type
    meta.ref_id = _ref_value(ref_id)
    meta.updated_at = utcnow()
    db.flush()
    return meta


def attach_many(db: Session, file_ids: Iterable[str], user: Any, ref_type: str, ref_id: Any, *,
                kinds: Iterable[str] | None = None, max_files: int = 20) -> list[StoredFile]:
    """Mehrere Dateien anhängen (z. B. Nachrichtenanhänge); alle oder keine (Ausnahme bricht ab)."""
    ids = list(dict.fromkeys(file_ids))
    if len(ids) > max_files:
        raise FileError(422, "too_many_files", f"Höchstens {max_files} Dateien.")
    return [attach(db, i, user, ref_type, ref_id, kinds=kinds) for i in ids]


def detach(db: Session, file_id: str) -> StoredFile | None:
    """Löst die Bindung (Datei bleibt erhalten und wird nach 24 h ohne neue Bindung von der Wartung gelöscht)."""
    meta = get_file(db, file_id)
    if meta is None:
        return None
    meta.ref_type = None
    meta.ref_id = None
    meta.updated_at = utcnow()
    db.flush()
    return meta


def delete(db: Session, file_id: str, user: Any = None, *, hard: bool = False) -> bool:
    """Löscht eine Datei: weich (``deleted_at``, Inhalt wird nach 30 Tagen entfernt) oder mit ``hard=True`` sofort.

    Rechte prüft der Aufrufer (Feature) – ``user`` dient nur dem Protokoll. Ohne Commit; beim harten Löschen wird
    der Inhalt erst nach erfolgreichem Commit (spätestens durch die Wartung) entfernt.
    """
    meta = get_file(db, file_id, include_deleted=True)
    if meta is None:
        return False
    if hard:
        db.delete(meta)
        db.flush()
        _unlink_later(db, [meta.id])
    elif meta.deleted_at is None:
        meta.deleted_at = utcnow()
        db.flush()
    return True


def delete_many(db: Session, file_ids: Iterable[str], user: Any = None, *, hard: bool = False) -> int:
    return sum(1 for i in dict.fromkeys(file_ids) if delete(db, i, user, hard=hard))


def delete_for_ref(db: Session, ref_type: str, ref_id: Any, *, hard: bool = False) -> int:
    """Alle an ein Objekt gebundenen Dateien löschen (z. B. beim Löschen einer Nachricht/eines Materials)."""
    ids = list(db.scalars(select(StoredFile.id).where(StoredFile.ref_type == ref_type,
                                                       StoredFile.ref_id == str(ref_id))))
    return delete_many(db, ids, hard=hard)


def duplicate(db: Session, file_id: str, user: Any, purpose: str | None = None) -> StoredFile:
    """Kopie mit neuem Datenschlüssel und neuem Eigentümer (z. B. Material in einen anderen Kurs übernehmen,
    Anhang weiterleiten). Rechte am Original prüft der Aufrufer; Quote und Typprüfung gelten erneut."""
    meta = get_file(db, file_id)
    if meta is None:
        raise _not_found()
    purpose = _check_purpose(purpose or meta.purpose)
    _check_quota(db, user, meta.size)
    sink = UploadSink(max(max_upload_bytes(purpose), meta.size))
    try:
        for block in iter_plaintext(meta):
            sink.write(block)
        sink.finish()
        if sink.sha256 != meta.sha256:
            raise FileError(500, "decrypt_failed", "Die Datei ist beschädigt (Prüfsumme).")
        return _finalize(db, user, sink, meta.filename, meta.content_type, purpose)
    finally:
        sink.discard()


def _unlink_later(db: Session, ids: list[str]) -> None:
    """Entfernt Inhalte nach dem Commit der Session (bei Rollback bleiben sie für die Wartung liegen)."""
    from sqlalchemy import event

    def _after_commit(_session: Session) -> None:
        for file_id in ids:
            _unlink_blob(file_id)

    event.listen(db, "after_commit", _after_commit, once=True)


def _unlink_blob(file_id: str) -> bool:
    try:
        blob_path(file_id).unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError:
        log.warning("Inhalt der Datei %s konnte nicht gelöscht werden", file_id)
        return False


# =========================================================================== Wartung
_last_gc = 0.0
_gc_lock = threading.Lock()


def cleanup(now: datetime | None = None, *, force_gc: bool = False) -> dict[str, int]:
    """Wartung: nicht angehängte Uploads > 24 h und gelöschte Dateien > 30 Tage endgültig entfernen,
    liegengebliebene Temp-Dateien und Inhalte ohne Datenbankeintrag aufräumen."""
    now = now or utcnow()
    orphan_cutoff = now - timedelta(hours=ORPHAN_HOURS)
    purge_cutoff = now - timedelta(days=PURGE_DAYS)
    with session_scope() as db:
        orphan_ids = list(db.scalars(select(StoredFile.id).where(
            StoredFile.ref_type.is_(None), StoredFile.deleted_at.is_(None),
            func.coalesce(StoredFile.updated_at, StoredFile.created_at) < orphan_cutoff)))
        purge_ids = list(db.scalars(select(StoredFile.id).where(StoredFile.deleted_at.is_not(None),
                                                                 StoredFile.deleted_at < purge_cutoff)))
        ids = orphan_ids + purge_ids
        for start in range(0, len(ids), 500):
            db.execute(sa_delete(StoredFile).where(StoredFile.id.in_(ids[start:start + 500])))
    removed = sum(1 for i in ids if _unlink_blob(i))
    result = {"files_orphaned": len(orphan_ids), "files_purged": len(purge_ids), "file_blobs_removed": removed}
    result["file_blobs_gc"] = gc_blobs(force=force_gc)
    if any(result.values()):
        log.info("Dateiablage-Wartung: %s", result)
    return result


def gc_blobs(force: bool = False) -> int:
    """Entfernt Inhalte ohne Datenbankeintrag und alte Temp-Dateien (höchstens alle 12 h, ``force`` sofort)."""
    global _last_gc
    root = files_root()
    if not root.is_dir():
        return 0
    with _gc_lock:
        if not force and _last_gc and time.monotonic() - _last_gc < BLOB_GC_HOURS * 3600:
            return 0
        _last_gc = time.monotonic()
    stale = time.time() - STALE_TMP_HOURS * 3600
    removed = 0
    candidates: list[Path] = []
    for d1 in _scandir(root):
        if d1.name == "tmp" and d1.is_dir():
            for f in _scandir(Path(d1.path)):
                if f.name.endswith(".tmp") and _mtime(f) < stale:
                    removed += _remove(Path(f.path))
            continue
        if not (len(d1.name) == 2 and d1.is_dir()):
            continue
        for d2 in _scandir(Path(d1.path)):
            if not (len(d2.name) == 2 and d2.is_dir()):
                continue
            for f in _scandir(Path(d2.path)):
                if f.name.endswith(".tmp"):
                    if _mtime(f) < stale:
                        removed += _remove(Path(f.path))
                elif ID_RE.match(f.name) and _mtime(f) < stale:
                    candidates.append(Path(f.path))
    with session_scope() as db:
        for start in range(0, len(candidates), 500):
            chunk = candidates[start:start + 500]
            known = set(db.scalars(select(StoredFile.id).where(StoredFile.id.in_([p.name for p in chunk]))))
            for p in chunk:
                if p.name not in known:
                    removed += _remove(p)
    return removed


def _scandir(path: Path) -> list[os.DirEntry]:
    try:
        with os.scandir(path) as it:
            return list(it)
    except OSError:
        return []


def _mtime(entry: os.DirEntry) -> float:
    try:
        return entry.stat().st_mtime
    except OSError:
        return time.time()


def _remove(path: Path) -> int:
    try:
        path.unlink()
        return 1
    except OSError:
        return 0


# =========================================================================== Schlüsselrotation
def _rewrap_files(db: Session) -> int:
    """Rotation: Dateinamen-Token und Kopf jedes Inhalts mit dem aktiven Master-Schlüssel neu wrappen."""
    active = crypto.active_key_id()
    changed = 0
    last = ""
    while True:
        rows = list(db.scalars(select(StoredFile).where(StoredFile.id > last).order_by(StoredFile.id).limit(200)))
        if not rows:
            break
        for meta in rows:
            last = meta.id
            touched = False
            if meta.filename_token and crypto.key_id_of(meta.filename_token) != active:
                meta.filename_token = crypto.rewrap(meta.filename_token)  # type: ignore[assignment]
                touched = True
            if meta.key_id != active:
                try:
                    crypto.rewrap_stream_file(blob_path(meta.id))
                except FileNotFoundError:
                    log.warning("Rotation: Inhalt der Datei %s fehlt", meta.id)
                meta.key_id = active
                touched = True
            changed += touched
        db.flush()
    return changed


crypto.register_rewrap("stored_files", _rewrap_files)


def verify_all(limit: int | None = None) -> dict[str, Any]:
    """Prüft alle Inhalte (Entschlüsselung + Prüfsumme) – für ``cli verify-files`` nach Restore/Umzug."""
    result: dict[str, Any] = {"ok": 0, "missing": [], "corrupt": []}
    with session_scope() as db:
        stmt = select(StoredFile).where(StoredFile.deleted_at.is_(None)).order_by(StoredFile.created_at)
        if limit:
            stmt = stmt.limit(limit)
        for meta in db.scalars(stmt):
            try:
                sha = hashlib.sha256()
                for block in iter_plaintext(meta):
                    sha.update(block)
                if sha.hexdigest() != meta.sha256:
                    result["corrupt"].append(meta.id)
                else:
                    result["ok"] += 1
            except FileError as exc:
                (result["missing"] if exc.code == "blob_missing" else result["corrupt"]).append(meta.id)
    return result


def limits_info(db: Session, user: Any, purpose: str | None = None) -> dict[str, Any]:
    """Grenzen und Allowlist für das Frontend (``GET /files/limits``)."""
    purpose = _check_purpose(purpose) if purpose else None
    rules = purpose_rules(purpose) if purpose else Purpose(DEFAULT_PURPOSE)
    kinds = [k for k in _KIND_LIST if (rules.kinds is None or k.key in rules.kinds)
             and (not k.opt_in or k.key in rules.extra)]
    quota = quota_bytes(user) if _is_real_user(user) else None
    return {
        "max_upload_bytes": max_upload_bytes(purpose),
        "quota_bytes": quota,
        "used_bytes": usage_bytes(db, user.id) if _is_real_user(user) else 0,
        "accept": ",".join(e for k in kinds for e in k.extensions),
        "kinds": [{"key": k.key, "label": k.label, "mime": k.mime, "extensions": list(k.extensions),
                   "group": k.group, "inline": k.inline} for k in kinds],
        "virus_scan": bool(config.clamav_host),
    }


def may_upload(user: Any) -> bool:
    perms = getattr(user, "permissions", None) or set()
    return bool(perms & UPLOAD_PERMISSIONS)


def list_own(db: Session, user: Any, *, purpose: str | None = None, unattached: bool = False,
             limit: int = 100) -> list[StoredFile]:
    stmt = select(StoredFile).where(StoredFile.owner_user_id == user.id, StoredFile.deleted_at.is_(None))
    if purpose:
        stmt = stmt.where(StoredFile.purpose == purpose)
    if unattached:
        stmt = stmt.where(StoredFile.ref_type.is_(None))
    return list(db.scalars(stmt.order_by(StoredFile.created_at.desc()).limit(limit)))
