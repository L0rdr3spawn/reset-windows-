"""Lernentwicklungsbericht als PDF (A4, mehrere Seiten) – Grundlage für Zeugnisbemerkungen und das
Lernentwicklungsgespräch. Aufbau: Kopf, je Rahmen und Bereich die Kompetenzen mit Stufenkästchen (Lehrkraft) und
Selbsteinschätzung, Kommentare, Abzeichen, Lernplan, Platz für Bemerkungen. Beobachtungsnotizen kommen nie hinein.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from .pdf_simple import A4, MARGIN, Page, render, text_width

TITLE_WIDTH = 300.0
BOX = 9.0
LINE = 11.0


def _wrap(text: str, width: float, size: float, bold: bool = False) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if cur and text_width(cand, size, bold) > width:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines or [""]


def _de(day: str) -> str:
    try:
        return date.fromisoformat(day[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return day


class _Doc:
    def __init__(self, header: str) -> None:
        self.pages: list[Page] = []
        self.header = header
        self.page = self._new()

    def _new(self) -> Page:
        p = Page()
        self.pages.append(p)
        p.text(MARGIN, A4[1] - 30, self.header, 8, gray=0.45)
        p.text(A4[0] - MARGIN - 40, 28, f"Seite {len(self.pages)}", 8, gray=0.45)
        p.text(MARGIN, 28, "Vertraulich – nur für Lehrkräfte und Eltern bestimmt", 8, gray=0.45)
        return p

    def room(self, height: float) -> None:
        if self.page.y - height < MARGIN:
            self.page = self._new()

    def para(self, text: str, size: float = 10, bold: bool = False, gap: float = 4, gray: float = 0.0,
             x: float = MARGIN, width: float = 0.0) -> None:
        width = width or (A4[0] - MARGIN - x)
        for line in _wrap(text, width, size, bold):
            self.room(size * 1.4)
            self.page.text(x, self.page.y, line, size, bold, gray)
            self.page.y -= size * 1.35
        self.page.y -= gap

    def squares(self, x: float, y: float, filled: int, total: int) -> None:
        for i in range(total):
            bx = x + i * (BOX + 3)
            self.page.ops.append(b"0.35 G 0.6 w %.1f %.1f %.1f %.1f re S" % (bx, y, BOX, BOX))
            if i < filled:
                self.page.ops.append(b"0.25 g %.1f %.1f %.1f %.1f re f" % (bx + 1, y + 1, BOX - 2, BOX - 2))


def build_report(name: str, class_name: str, frameworks: Sequence[dict[str, Any]], badges: Sequence[dict[str, Any]],
                 plans: Sequence[dict[str, Any]], today: date) -> bytes:
    doc = _Doc(f"Lernentwicklungsbericht – {name}")
    p = doc.page
    p.text(MARGIN, p.y, "Lernentwicklungsbericht", 18, bold=True)
    p.y -= 26
    p.text(MARGIN, p.y, name, 13, bold=True)
    p.text(A4[0] - MARGIN - 150, p.y, f"Klasse {class_name}  ·  {today.strftime('%d.%m.%Y')}", 10)
    p.y -= 8
    p.line(MARGIN, p.y, A4[0] - MARGIN, p.y, 0.8)
    p.y -= 18
    if not frameworks:
        doc.para("Es sind noch keine Kompetenzrahmen angelegt.", 10)
    for fw in frameworks:
        n = len(fw["levels"])
        doc.room(70)
        doc.para(fw["name"], 13, bold=True, gap=2)
        doc.para(f"Eingeschätzt: {fw['assessed']} von {fw['total']} Kompetenzen  ·  Fortschritt "
                 f"{round(fw['progress'] * 100)} %", 9, gray=0.35, gap=2)
        legend = "   ".join(f"{i + 1} = {lv}" for i, lv in enumerate(fw["levels"]))
        doc.para("Stufen: " + legend, 8, gray=0.35, gap=8)
        for area in fw["areas"]:
            doc.room(60)
            doc.para(f"{area['name']}  ({round(area['progress'] * 100)} %)", 11, bold=True, gap=3)
            for c in area["competencies"]:
                t, s = c.get("teacher"), c.get("self")
                lines = _wrap(c["title"], TITLE_WIDTH, 9)
                comment = (t or {}).get("comment", "")
                extra = _wrap("Kommentar: " + comment[:240], A4[0] - 2 * MARGIN - 12, 8) if comment else []
                doc.room(len(lines) * LINE + len(extra) * 10 + 8)
                top = doc.page.y
                for line in lines:
                    doc.page.text(MARGIN + 6, doc.page.y, line, 9)
                    doc.page.y -= LINE
                box_x = MARGIN + 6 + TITLE_WIDTH + 14
                doc.squares(box_x, top - 1, (t or {}).get("level", 0), n)
                right = box_x + n * (BOX + 3) + 6
                if s:
                    doc.page.text(right, top, f"Ich: {s['level']}", 8, gray=0.35)
                if t:
                    doc.page.text(right, top - 9, _de(t["date"]), 7, gray=0.5)
                for line in extra:
                    doc.page.text(MARGIN + 12, doc.page.y, line, 8, gray=0.35)
                    doc.page.y -= 10
                doc.page.y -= 3
            doc.page.y -= 6
    if badges:
        doc.room(50)
        doc.para("Abzeichen", 12, bold=True, gap=3)
        for b in badges:
            doc.para(f"{b['name']} ({_de(b['date'])})" + (f" – {b['description']}" if b.get("description") else ""),
                     9, x=MARGIN + 6, gap=1)
        doc.page.y -= 6
    if plans:
        done = sum(1 for x in plans if x["status"] == "erledigt")
        doc.room(50)
        doc.para("Lernplan", 12, bold=True, gap=3)
        doc.para(f"{done} von {len(plans)} Zielen erledigt.", 9, gap=2)
        for x in [x for x in plans if x["status"] != "erledigt"][:12]:
            due = f"  (bis {_de(x['due_date'])})" if x["due_date"] else ""
            doc.para("• " + x["title"] + due, 9, x=MARGIN + 6, gap=1)
        doc.page.y -= 6
    doc.room(130)
    doc.para("Bemerkungen zum Lernentwicklungsgespräch", 12, bold=True, gap=6)
    for _ in range(5):
        doc.room(24)
        doc.page.line(MARGIN, doc.page.y - 6, A4[0] - MARGIN, doc.page.y - 6, 0.4, 0.5)
        doc.page.y -= 22
    return render(doc.pages, f"Lernentwicklungsbericht {name}")
