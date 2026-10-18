"""Sperre bei ungültiger Lizenz (``licensing``, Stufe ``locked``): jede API-Anfrage wird abgewiesen.

Offen bleiben nur Anmeldung und Abmeldung (``/api/v1/auth/…``), die Lizenzrouten (``/api/v1/license…``, die selbst das
Recht ``license.manage`` verlangen) und die Version; außerhalb der API ``/healthz``, ``/metrics`` und die Dateien der
Oberfläche (die zeigt anhand von ``/auth/me`` die Sperrseite). Öffentliche Kalender-Feeds (``/ical/``) sind ebenfalls
zu. Ohne Durchsetzung (``SM_LICENSE_ENFORCE``, in ``SM_MODE=production`` immer an) tut die Middleware nichts.

Die Prüfung steht hier und nicht in der Anmeldung (``deps.authenticate``), weil sie auch Routen ohne Anmeldung und
künftig neu hinzukommende Routen erfasst: neue Routen sind automatisch gesperrt.
"""
from __future__ import annotations

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from . import licensing
from .config import config

API = "/api/v1"
OPEN_WHEN_LOCKED = (f"{API}/auth/", f"{API}/license", f"{API}/version")
CODE = "license_locked"


def blocked_when_locked(path: str) -> bool:
    """Ist dieser Pfad bei gesperrter Lizenz zu?"""
    if path.startswith(OPEN_WHEN_LOCKED):
        return False
    return path.startswith("/api/") or path == "/api" or path.startswith("/ical/")


class LicenseLockMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not config.license_enforce or not blocked_when_locked(scope.get("path", "")) \
                or not licensing.is_locked():
            await self.app(scope, receive, send)
            return
        body = json.dumps({"detail": CODE, "code": CODE,
                           "message": f"Die Anwendung ist gesperrt: {licensing.lock_message()} Bitte wenden Sie sich "
                                      "an die Schulleitung bzw. Administration."}, ensure_ascii=False).encode("utf-8")
        await send({"type": "http.response.start", "status": 403,
                    "headers": [(b"content-type", b"application/json; charset=utf-8"),
                                (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})
