"""PDF-Ausgabe des Formular-Baukastens: leer zum Ausdrucken oder ausgefüllt zum Archiv (mehrseitig, A4).

Baut auf :mod:`schulmanager.server.pdf_simple` auf (Helvetica, WinAnsi). Nicht darstellbare Zeichen werden zu ``?``.
"""
from __future__ import annotations

from typing import Any, Optional

from schulmanager.forms import display_value, fmt_date

from ..branding import PRODUCT_NAME
from .pdf_simple import A4, MARGIN, Page, render, text_width

WIDTH = A4[0] - 2 * MARGIN
BOTTOM = 70.0


class _Doc:
    def __init__(self, header: str) -> None:
        self.header = header
        self.pages: list[Page] = []
        self.p = self._new()

    def _new(self) -> Page:
        page = Page()
        page.text(MARGIN, page.y, self.header, 8, gray=0.4)
        page.y -= 22
        self.pages.append(page)
        return page

    def need(self, height: float) -> None:
        if self.p.y - height < BOTTOM:
            self.p = self._new()

    def lines(self, text: str, size: float, width: float = WIDTH, bold: bool = False) -> list[str]:
        out: list[str] = []
        for paragraph in (text or "").split("\n"):
            line = ""
            for word in paragraph.split():
                cand = f"{line} {word}".strip()
                if text_width(cand, size, bold) > width and line:
                    out.append(line)
                    line = word
                else:
                    line = cand
            out.append(line)
        return out

    def write(self, text: str, size: float = 10, bold: bool = False, gray: float = 0.0, x: float = MARGIN,
              width: float = WIDTH, gap: float = 4) -> None:
        for line in self.lines(text, size, width, bold):
            self.need(size * 1.4)
            self.p.text(x, self.p.y, line, size, bold, gray)
            self.p.y -= size * 1.4
        self.p.y -= gap

    def label(self, text: str, required: bool = False) -> None:
        self.need(40)
        self.p.text(MARGIN, self.p.y, text + (" *" if required else ""), 8.5, gray=0.3)
        self.p.y -= 14

    def line_field(self, value: str = "", width: float = WIDTH, x: float = MARGIN) -> None:
        self.need(22)
        if value:
            self.p.text(x + 2, self.p.y + 3, value[:int(width / 5)], 10)
        self.p.line(x, self.p.y, x + width, self.p.y, 0.5)
        self.p.y -= 20

    def check(self, label: str, checked: bool, x: float = MARGIN) -> None:
        self.need(18)
        self.p.box(x, self.p.y - 2, 10, 10, checked=checked)
        self.p.text(x + 16, self.p.y, label, 10)
        self.p.y -= 17

    def finish(self, title: str, footer: str) -> bytes:
        total = len(self.pages)
        for i, page in enumerate(self.pages, 1):
            page.text(MARGIN, 36, f"{footer}", 7.5, gray=0.45)
            label = f"Seite {i} von {total}"
            page.text(A4[0] - MARGIN - text_width(label, 7.5), 36, label, 7.5, gray=0.45)
        return render(self.pages, title)


def _fill_field(doc: _Doc, f: dict, value: Any, filled: bool, ctx: dict) -> None:
    ftype = f["type"]
    req = bool(f.get("required")) and not filled
    shown = display_value(f, value) if filled else ""
    if ftype in ("text", "number", "date", "student"):
        doc.label(f["label"] if ftype != "student" else "Name der Schülerin / des Schülers · Klasse", req)
        if ftype == "student":
            shown = ctx.get("student") or ""
        doc.line_field(shown)
    elif ftype == "textarea":
        doc.label(f["label"], req)
        if shown:
            doc.write(shown, 10, gap=6)
        else:
            for _ in range(4):
                doc.line_field()
    elif ftype == "daterange":
        doc.label(f["label"], req)
        d = value if isinstance(value, dict) else {}
        half = (WIDTH - 16) / 2
        doc.need(24)
        y0 = doc.p.y
        doc.p.text(MARGIN, y0, "vom", 8, gray=0.35)
        doc.p.text(MARGIN + half + 16, y0, "bis einschließlich", 8, gray=0.35)
        doc.p.y -= 14
        if filled and d.get("from"):
            doc.p.text(MARGIN + 2, doc.p.y + 3, fmt_date(d["from"]), 10)
            doc.p.text(MARGIN + half + 18, doc.p.y + 3, fmt_date(d.get("to") or d["from"]), 10)
        doc.p.line(MARGIN, doc.p.y, MARGIN + half, doc.p.y, 0.5)
        doc.p.line(MARGIN + half + 16, doc.p.y, MARGIN + WIDTH, doc.p.y, 0.5)
        doc.p.y -= 20
    elif ftype in ("select", "multiselect"):
        doc.label(f["label"], req)
        chosen = set(value if isinstance(value, list) else [value]) if filled else set()
        for option in f.get("options", []):
            doc.check(option, option in chosen)
    elif ftype == "yesno":
        doc.label(f["label"], req)
        doc.need(18)
        y = doc.p.y
        doc.p.box(MARGIN, y - 2, 10, 10, checked=filled and value is True)
        doc.p.text(MARGIN + 16, y, "Ja", 10)
        doc.p.box(MARGIN + 70, y - 2, 10, 10, checked=filled and value is False)
        doc.p.text(MARGIN + 86, y, "Nein", 10)
        doc.p.y -= 20
    elif ftype == "confirm":
        doc.need(30)
        doc.p.box(MARGIN, doc.p.y - 2, 10, 10, checked=filled and bool(value))
        doc.p.text(MARGIN + 16, doc.p.y, f["label"], 10, bold=True)
        doc.p.y -= 15
        if f.get("text"):
            doc.write(f["text"], 9, x=MARGIN + 16, width=WIDTH - 16, gray=0.2, gap=6)
        else:
            doc.p.y -= 4
    elif ftype == "signature":
        doc.p.y -= 8
        half = (WIDTH - 16) / 2
        doc.need(46)
        y0 = doc.p.y
        if filled and isinstance(value, dict):
            doc.p.text(MARGIN + 2, y0 - 14 + 3, fmt_date(value.get("date", "")), 10)
            doc.p.text(MARGIN + half + 18, y0 - 14 + 3, value.get("name", ""), 10)
        doc.p.text(MARGIN, y0, "Ort, Datum", 8, gray=0.35)
        doc.p.text(MARGIN + half + 16, y0, f["label"], 8, gray=0.35)
        doc.p.line(MARGIN, y0 - 14, MARGIN + half, y0 - 14, 0.5)
        doc.p.line(MARGIN + half + 16, y0 - 14, MARGIN + WIDTH, y0 - 14, 0.5)
        doc.p.y = y0 - 22
        if filled and isinstance(value, dict):
            doc.write(f"online bestätigt (Name und Datum wurden im {PRODUCT_NAME} erfasst)", 7.5, gray=0.4, gap=6)
    elif ftype == "file":
        doc.label(f["label"], req)
        if filled:
            doc.write(shown or "keine Anlage", 10, gap=6)
        else:
            doc.check("Anlage liegt bei", False)
    elif ftype == "periods":
        doc.label(f["label"], req)
        count = int(ctx.get("periods") or 8)
        chosen = {int(p) for p in value} if filled and isinstance(value, list) else set()
        doc.need(34)
        y = doc.p.y
        for i in range(count):
            x = MARGIN + i * 40
            doc.p.box(x, y - 2, 10, 10, checked=i in chosen)
            doc.p.text(x + 14, y, f"{i + 1}.", 9)
        doc.p.y -= 22


def _build(doc: _Doc, title: str, description: str, fields: list[dict], *, intro: str = "",
           answers: Optional[dict[str, Any]] = None, meta: Optional[dict[str, Any]] = None, student_text: str = "",
           periods: int = 8, history: Optional[list[str]] = None) -> None:
    filled = answers is not None
    doc.p.y -= 4
    doc.write(title, 18, bold=True, gap=2)
    if description:
        doc.write(description, 9.5, gray=0.25, gap=6)
    if intro:
        doc.write(intro, 9.5, gap=8)
    if not filled:
        doc.write(f"Bitte ausfüllen, unterschreiben und in der Schule abgeben oder als Foto/PDF im {PRODUCT_NAME} "
                  "hochladen. Mit * markierte Felder sind Pflicht.", 8.5, gray=0.35, gap=10)
    if meta:
        for key, val in meta.items():
            if val:
                doc.write(f"{key}: {val}", 9.5, gap=1)
        doc.p.y -= 8
        doc.p.line(MARGIN, doc.p.y + 4, MARGIN + WIDTH, doc.p.y + 4, 0.4, 0.6)
        doc.p.y -= 8
    ctx = {"student": student_text, "periods": periods}
    for f in fields:
        _fill_field(doc, f, (answers or {}).get(f["id"]), filled, ctx)
    if history:
        doc.p.y -= 10
        doc.write("Verlauf", 11, bold=True, gap=2)
        for line in history:
            doc.write(line, 9, gap=0)


def render_form(title: str, description: str, fields: list[dict], *, school_name: str = "", intro: str = "",
                answers: Optional[dict[str, Any]] = None, meta: Optional[dict[str, Any]] = None,
                student_text: str = "", periods: int = 8, version: int = 1, history: Optional[list[str]] = None,
                ) -> bytes:
    """Formular als PDF. Ohne ``answers`` leer zum Ausdrucken (Schreiblinien, Kästchen), sonst ausgefüllt.

    ``meta`` (nur ausgefüllt): ``{"Status": …, "Eingereicht von": …}`` als Kopfblock; ``history`` = Verlaufszeilen."""
    doc = _Doc(school_name or "Schule")
    _build(doc, title, description, fields, intro=intro, answers=answers, meta=meta, student_text=student_text,
           periods=periods, history=history)
    return doc.finish(title, f"{title} · Version {version}")


def render_forms(title: str, items: list[dict], *, school_name: str = "") -> bytes:
    """Mehrere ausgefüllte Formulare in einem PDF (jedes beginnt auf einer neuen Seite). ``items``: Argumente von
    :func:`_build` (``title``, ``description``, ``fields``, ``answers``, ``meta`` …)."""
    doc = _Doc(school_name or "Schule")
    for i, item in enumerate(items):
        if i:
            doc.p = doc._new()
        _build(doc, item["title"], item.get("description", ""), item["fields"], intro=item.get("intro", ""),
               answers=item.get("answers"), meta=item.get("meta"), student_text=item.get("student_text", ""),
               periods=item.get("periods", 8), history=item.get("history"))
    return doc.finish(title, title)
