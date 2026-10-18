"""FastAPI-Anwendung des Schulmanagers.

Start: ``uvicorn schulmanager.server.app:app --host 0.0.0.0 --port 8000`` (``app`` wird beim ersten
Zugriff über :func:`create_app` erzeugt). Tests: ``create_app()`` nach dem Setzen der Umgebung.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response
from sqlalchemy import func, select
from starlette.middleware.gzip import GZipMiddleware

from ..branding import PRODUCT_NAME
from . import db as dbmod
from . import runtime
from .config import APP_VERSION, config
from .docs_ui import add_docs_routes
from .license_lock import LicenseLockMiddleware
from .logging_setup import request_id_var, setup_logging
from .metrics import metrics
from .middleware import CoreMiddleware, mask_path
from .proxy import TrustedProxyMiddleware
from .security import constant_equals
from .store import StoreError

log = logging.getLogger("schulmanager.app")

API_PREFIX = "/api/v1"
CORE_ROUTERS = ("auth", "users", "history", "admin", "me", "events", "system", "oidc")
RESERVED_PREFIXES = frozenset({"api", "healthz", "metrics", "ical"})
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await runtime.startup()
    log.info("Schulmanager %s gestartet (%s, DB %s)", APP_VERSION, config.env, config.db_kind)
    try:
        yield
    finally:
        await runtime.shutdown()
        log.info("Schulmanager beendet")


def _route_modules() -> list[str]:
    from . import routes

    names = sorted(m.name for m in pkgutil.iter_modules(routes.__path__) if not m.name.startswith("_"))
    core = [n for n in CORE_ROUTERS if n in names]
    return core + [n for n in names if n not in core]


def include_routers(app: FastAPI) -> list[str]:
    """Bindet alle ``routes/*.py`` mit ``router`` (unter /api/v1) bzw. ``public_router`` (ohne Präfix) ein."""
    loaded = []
    for name in _route_modules():
        try:
            module = importlib.import_module(f"schulmanager.server.routes.{name}")
        except Exception:
            if config.is_production:
                raise
            log.exception("Router-Modul routes/%s.py konnte nicht geladen werden – wird übersprungen", name)
            continue
        router = getattr(module, "router", None)
        public = getattr(module, "public_router", None)
        if router is not None:
            app.include_router(router, prefix=API_PREFIX)
        if public is not None:
            app.include_router(public)
        if router is not None or public is not None:
            loaded.append(name)
    return loaded


def frontend_dir() -> Path | None:
    path = Path(config.frontend_dist)
    if not path.is_absolute() and not path.exists():
        path = _PACKAGE_ROOT / path
    return path if (path / "index.html").is_file() else None


_NO_FRONTEND = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{PRODUCT_NAME}</title></head>
<body style="font-family:system-ui;max-width:40rem;margin:4rem auto;padding:0 1rem">
<h1>{PRODUCT_NAME}</h1><p>Der Server läuft, das Frontend ist aber noch nicht gebaut
(<code>cd frontend &amp;&amp; npm ci &amp;&amp; npm run build</code>).</p>
<p>Status: <a href="/healthz">/healthz</a></p></body></html>"""


def _add_infra_routes(app: FastAPI) -> None:
    @app.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
    def healthz() -> JSONResponse:
        try:
            dbmod.check_db()
            db_ok = True
        except Exception:  # noqa: BLE001
            log.exception("Health-Check: Datenbank nicht erreichbar")
            db_ok = False
        body: dict[str, Any] = {"status": "ok" if db_ok else "error", "db": "ok" if db_ok else "error",
                                "version": APP_VERSION, "started": runtime.is_started()}
        if runtime.is_started():
            from .store import get_store

            body["plan_version"] = get_store().version
        body["node"] = config.node_id                                   # UPDATES-HA
        return JSONResponse(body, status_code=200 if db_ok else 503)

    # >>> UPDATES-HA: Bereitschaft für den Lastausgleich. 503, solange der Update-Agent diesen Knoten „leerlaufen“ lässt
    # (Datei ``drain-<SM_NODE_ID>.flag`` im Datenordner) oder die App nicht bereit ist; ``/healthz`` bleibt davon unberührt.
    @app.api_route("/healthz/ready", methods=["GET", "HEAD"], include_in_schema=False)
    def healthz_ready() -> JSONResponse:
        draining = (config.data_dir / f"drain-{config.node_id}.flag").exists()
        try:
            dbmod.check_db()
            db_ok = True
        except Exception:  # noqa: BLE001
            db_ok = False
        ready = db_ok and runtime.is_started() and not draining
        return JSONResponse({"ready": ready, "draining": draining, "db": db_ok, "node": config.node_id},
                            status_code=200 if ready else 503)
    # <<< UPDATES-HA

    @app.get("/metrics", include_in_schema=False)
    def prometheus(request: Request) -> PlainTextResponse:
        token = config.metrics_token
        if token and not constant_equals(request.headers.get("authorization", ""), f"Bearer {token}"):
            raise HTTPException(401, "not_authenticated")
        from .db_models import SchoolVersion, User, UserSession
        from .events import bus

        gauges: dict[str, tuple[str, list]] = {
            "schulmanager_info": ("Versionsinformation", [({"version": APP_VERSION, "env": config.env,
                                                            "db": config.db_kind}, 1)]),
            "schulmanager_sse_clients": ("Verbundene SSE-Clients", [({}, bus.client_count)]),
        }
        jobs = runtime.optional_module("jobs")
        running = getattr(jobs, "running_count", None) if jobs else None
        if callable(running):
            try:
                gauges["schulmanager_jobs_running"] = ("Laufende Generator-Jobs", [({}, int(running()))])
            except Exception:  # noqa: BLE001
                log.exception("Metriken: jobs.running_count() fehlgeschlagen")
        if runtime.is_started():
            from .store import get_store

            store = get_store()
            gauges["schulmanager_school_version"] = ("Aktuelle Version des Planungsdokuments",
                                                     [({}, store.version)])
            try:
                with dbmod.SessionLocal() as db:
                    rows = db.execute(select(User.role, User.active, func.count(User.id))
                                      .group_by(User.role, User.active)).all()
                    gauges["schulmanager_users"] = ("Benutzerkonten nach Rolle", [
                        ({"role": r, "active": "true" if a else "false"}, n) for r, a, n in rows])
                    now = dbmod.utcnow()
                    sessions = db.scalar(select(func.count(UserSession.id)).where(UserSession.expires_at > now))
                    gauges["schulmanager_sessions_active"] = ("Aktive Sitzungen", [({}, sessions or 0)])
                    versions = db.scalar(select(func.count(SchoolVersion.id)))
                    gauges["schulmanager_school_versions_stored"] = ("Gespeicherte Planversionen",
                                                                     [({}, versions or 0)])
            except Exception:  # noqa: BLE001
                log.exception("Metriken: Datenbankabfrage fehlgeschlagen")
        return PlainTextResponse(metrics.render(gauges), media_type="text/plain; version=0.0.4; charset=utf-8")

    add_docs_routes(app)

    @app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    def api_not_found(rest: str) -> JSONResponse:
        return JSONResponse({"detail": "Nicht gefunden"}, status_code=404)


def _add_spa_routes(app: FastAPI) -> None:
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> Response:
        if full_path.split("/", 1)[0] in RESERVED_PREFIXES:
            return JSONResponse({"detail": "Nicht gefunden"}, status_code=404)
        dist = frontend_dir()
        if dist is None:
            if full_path in ("", "index.html"):
                return HTMLResponse(_NO_FRONTEND)
            return JSONResponse({"detail": "Frontend nicht gebaut"}, status_code=404)
        if full_path:
            root = dist.resolve()
            candidate = (dist / full_path).resolve()
            if candidate.is_file() and root in candidate.parents:
                headers = {"Cache-Control": "public, max-age=31536000, immutable"} \
                    if full_path.startswith("assets/") else {"Cache-Control": "public, max-age=3600"}
                return FileResponse(candidate, headers=headers)
            if full_path.startswith("assets/"):
                return JSONResponse({"detail": "Nicht gefunden"}, status_code=404)
        return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})


def _add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StoreError)
    async def store_error(_request: Request, exc: StoreError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.error("Unbehandelter Fehler bei %s %s", request.method, mask_path(request.url.path), exc_info=exc)
        return JSONResponse({"detail": "Interner Serverfehler", "request_id": request_id_var.get()},
                            status_code=500)


class SelectiveGZipMiddleware(GZipMiddleware):
    """GZip für alle Antworten außer Datei-Downloads (``/api/v1/files/…``, Erweiterung 2).

    Hochgeladene Dateien (PDF, Bilder, Videos, ZIP, Office) sind meist schon komprimiert – erneutes Komprimieren
    kostet nur CPU und würde bei gestreamten Downloads ``Content-Length`` entfernen (kein Fortschrittsbalken).
    """

    SKIP_PREFIXES: tuple[str, ...] = (f"{API_PREFIX}/files/",)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http" and str(scope.get("path", "")).startswith(self.SKIP_PREFIXES):
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)


def create_app() -> FastAPI:
    """Erzeugt eine neue App (liest die Umgebung neu ein, setzt Laufzeitzustand zurück)."""
    config.reload()
    setup_logging()
    config.validate()
    runtime.reset()
    metrics.reset()
    dbmod.configure_engine()
    # Swagger/OpenAPI liefert docs_ui.py selbst aus (lokal, standardmäßig nur für Administratoren, S-15)
    app = FastAPI(title=f"{config.app_name} API", version=APP_VERSION, lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None,
                  description=f"REST-API von {PRODUCT_NAME} (Stundenplan, Vertretungsplan, Konten). Für Apps und KI-Werkzeuge: "
                              "die öffentliche API unter /api/v1/open mit API-Zugängen (Bereiche, Filter) – "
                              "Beschreibung unter /llms.txt und /api/v1/meta/openapi.json.",
                  openapi_tags=[{"name": "Öffentliche API", "description": "Versionierte API für Apps/KIs (Bearer-Zugang "
                                 "mit Bereichen und Filtern; nur lesen, optional Mitteilungen schreiben)."},
                                {"name": "API-Zugänge", "description": "Zugänge ausgeben, Nutzung ansehen, widerrufen."}])
    app.add_middleware(SelectiveGZipMiddleware, minimum_size=1024)
    app.add_middleware(LicenseLockMiddleware)   # gesperrte Lizenz: API für alle zu (innen, Kopfzeilen/Metriken bleiben)
    app.add_middleware(CoreMiddleware)
    app.add_middleware(TrustedProxyMiddleware)   # ganz außen: setzt Client-IP/Schema für alles dahinter
    _add_exception_handlers(app)
    app.state.routers = include_routers(app)
    _add_infra_routes(app)
    _add_spa_routes(app)
    return app


_app: FastAPI | None = None


def __getattr__(name: str) -> Any:
    """Lazy ``app`` für ``uvicorn schulmanager.server.app:app`` (PEP 562)."""
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
