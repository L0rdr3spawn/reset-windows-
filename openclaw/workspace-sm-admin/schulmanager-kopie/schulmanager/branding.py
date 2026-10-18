"""Produktmarke – einzige Stelle für den sichtbaren Produktnamen im Backend.

Nur die **sichtbare** Marke heißt ``Schulpuls``: PDF-Kopfzeilen, E-Mail-Betreffe und -Texte, OpenAPI-Titel,
``llms.txt``, Fehlermeldungen. Technische Namen bleiben: Python-Paket ``schulmanager``, Cookies ``sm_*``,
Umgebungsvariablen ``SM_*``, Webhook-Header ``X-Schulmanager-*``, Docker-Namen, Routen, Lizenzserver.
Frontend-Gegenstück: ``frontend/src/brand.ts``. ``SM_APP_NAME`` (``config.app_name``) überschreibt den Namen
weiterhin je Instanz (OpenAPI-Titel, TOTP-Aussteller, Kontakt-Mails); Standard ist :data:`PRODUCT_NAME`.
Logo-Quelle: ``frontend/src/assets/logo.svg``; Doku: ``docs/branding/README.md``.
"""
from __future__ import annotations

from typing import Any

#: Produktname (Grammatik: *der* Schulpuls – „im Schulpuls“, „den Schulpuls“).
PRODUCT_NAME = "Schulpuls"
#: Kurzform für enge Stellen.
PRODUCT_SHORT = "Puls"
#: Slogan für Briefe, Login und Doku.
TAGLINE = "Stundenplan, Klassenbuch und Nachrichten – im Takt der Schule."

#: Farben der Bildmarke (RGB 0–1), passend zu ``frontend/src/styles/tokens.css`` (``--primary`` hell, ``--warning`` dunkel).
LOGO_TILE = (0x1D / 255, 0x4E / 255, 0xD8 / 255)
LOGO_LINE = (1.0, 1.0, 1.0)
LOGO_DOT = (0xFB / 255, 0xBF / 255, 0x24 / 255)

#: Pulslinie aus ``logo.svg`` (Koordinaten 0–64, y nach unten): ``M11 37 h10 l6-18 l8 28 l6-10 h12``.
LOGO_POINTS: tuple[tuple[float, float], ...] = ((11, 37), (21, 37), (27, 19), (35, 47), (41, 37), (53, 37))
LOGO_DOT_CENTER: tuple[float, float] = (53, 37)
LOGO_DOT_RADIUS = 5.0
LOGO_STROKE = 6.0


def product_with_school(school_name: str | None) -> str:
    """„Schulpuls · Schulname“ – der eigene Schulname aus den Einstellungen bleibt und kommt dazu."""
    s = (school_name or "").strip()
    return f"{PRODUCT_NAME} · {s}" if s and s != PRODUCT_NAME else PRODUCT_NAME


def draw_logo(page: Any, x: float, y: float, size: float, *, color: tuple[float, float, float] | float = LOGO_TILE,
              dot: tuple[float, float, float] | float = LOGO_DOT) -> None:
    """Bildmarke ohne Kachel (Pulslinie in Primärfarbe, Punkt in Bernstein) auf eine ``server.pdf.Page``
    (``x``/``y`` = linke obere Ecke, y nach unten, Kantenlänge ``size``)."""
    k = size / 64
    page.polyline([(x + px * k, y + py * k) for px, py in LOGO_POINTS], width=LOGO_STROKE * k, color=color)
    page.circle(x + LOGO_DOT_CENTER[0] * k, y + LOGO_DOT_CENTER[1] * k, LOGO_DOT_RADIUS * k, fill=dot)


def draw_logo_simple(page: Any, x: float, y_top: float, size: float, gray: float = 0.15) -> None:
    """Bildmarke einfarbig (Graustufe) auf eine ``server.pdf_simple.Page`` (PDF-Koordinaten, y nach oben;
    ``y_top`` = obere Kante)."""
    k = size / 64
    page.polyline([(x + px * k, y_top - py * k) for px, py in LOGO_POINTS], width=LOGO_STROKE * k, gray=gray)
    page.disc(x + LOGO_DOT_CENTER[0] * k, y_top - LOGO_DOT_CENTER[1] * k, LOGO_DOT_RADIUS * k, gray=gray)
