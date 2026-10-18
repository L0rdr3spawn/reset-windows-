"""Swagger-UI/OpenAPI für Entwickelnde (S-15): lokal ausgeliefert, standardmäßig nur für angemeldete Administratoren.

* ``SM_ENABLE_DOCS=0``       – ``/api/docs`` und ``/api/openapi.json`` gibt es nicht.
* ``SM_ENABLE_DOCS=admin``   – nur angemeldete Administratoren (Sitzung oder API-Token) – Voreinstellung außerhalb
                               des ausdrücklichen Echtbetriebs.
* ``SM_ENABLE_DOCS=1``       – für alle (nur im Schulnetz sinnvoll; verrät die komplette Endpunktliste).

Die Oberfläche kommt aus ``static/swagger/`` (swagger-ui-dist, Apache-2.0) – es wird nichts von einem CDN geladen,
die CSP erlaubt nur ``'self'``. Die öffentliche API-Beschreibung (``/llms.txt``, ``/api/v1/meta/openapi.json``)
ist davon unabhängig.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from .config import config
from .deps import AuthUser, current_user

ASSET_DIR = Path(__file__).resolve().parent / "static" / "swagger"
ASSETS = {
    "swagger-ui.css": "text/css; charset=utf-8",
    "swagger-ui-bundle.js": "text/javascript; charset=utf-8",
    "favicon-32x32.png": "image/png",
    "LICENSE": "text/plain; charset=utf-8",
}
# Eigene Startdatei statt Inline-Skript, damit die CSP ohne 'unsafe-inline' für Skripte auskommt
_INIT_JS = """window.addEventListener('load', function () {
  window.ui = SwaggerUIBundle({
    url: '/api/openapi.json',
    dom_id: '#swagger-ui',
    deepLinking: true,
    persistAuthorization: false,
    presets: [SwaggerUIBundle.presets.apis],
    layout: 'BaseLayout'
  });
});
"""
_PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – API-Dokumentation</title>
<link rel="icon" href="/api/docs-assets/favicon-32x32.png">
<link rel="stylesheet" href="/api/docs-assets/swagger-ui.css"></head>
<body><div id="swagger-ui"></div>
<script src="/api/docs-assets/swagger-ui-bundle.js"></script>
<script src="/api/docs-assets/init.js"></script></body></html>"""


def docs_gate(user: AuthUser = Depends(current_user)) -> AuthUser:
    """Zugang zur Dokumentation: im Modus ``admin`` nur Administratoren."""
    if config.docs_mode == "admin" and user.role != "admin":
        raise HTTPException(403, "Die API-Dokumentation ist nur für Administratoren sichtbar.")
    return user


def add_docs_routes(app: FastAPI) -> None:
    """Muss vor dem Sammelpfad ``/api/{rest:path}`` registriert werden."""
    if config.docs_mode == "off":
        return

    gate = [] if config.docs_mode == "public" else [Depends(docs_gate)]

    @app.get("/api/openapi.json", include_in_schema=False, dependencies=gate)
    def openapi_json() -> JSONResponse:
        return JSONResponse(app.openapi(), headers={"Cache-Control": "no-store"})

    @app.get("/api/docs", include_in_schema=False, dependencies=gate)
    def swagger_page() -> HTMLResponse:
        return HTMLResponse(_PAGE.format(title=config.app_name), headers={"Cache-Control": "no-store"})

    @app.get("/api/docs-assets/init.js", include_in_schema=False)
    def swagger_init() -> Response:
        return Response(_INIT_JS, media_type="text/javascript; charset=utf-8")

    @app.get("/api/docs-assets/{name}", include_in_schema=False)
    def swagger_asset(name: str) -> FileResponse:
        media = ASSETS.get(name)
        if media is None or not (ASSET_DIR / name).is_file():
            raise HTTPException(404, "Nicht gefunden")
        return FileResponse(ASSET_DIR / name, media_type=media, headers={"Cache-Control": "public, max-age=86400"})
