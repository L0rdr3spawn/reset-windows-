"""ASGI-Middleware: Request-ID, Metriken, Access-Log, Security-Header."""
from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import config
from .logging_setup import request_id_var, truncate_ip
from .metrics import metrics

access_log = logging.getLogger("schulmanager.access")

_RID_RE = re.compile(r"^[A-Za-z0-9._\-]{1,64}$")

CSP_APP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
           "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; manifest-src 'self'; "
           "worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")
# Swagger-UI (nur /api/docs): komplett lokal ausgeliefert (static/swagger), nichts von Dritten (S-15)
CSP_DOCS = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")


def csp_for(path: str) -> str:
    """CSP der Seite. Nur Seiten (nicht ``/api/``) erhalten die Quellen der **aktiven** Anmeldedienste (Google/Apple);
    ohne aktiven Anbieter bleibt die Richtlinie wie sie ist – es wird nichts von Dritten geladen."""
    if path.startswith("/api/docs"):
        return CSP_DOCS
    if path.startswith(("/api/", "/ical/")):
        return CSP_APP
    from . import sso_providers

    return sso_providers.extend_csp(CSP_APP, sso_providers.csp_sources())


def mask_path(path: str) -> str:
    """Geheime Pfadbestandteile (iCal-Token) für Logs unkenntlich machen."""
    if path.startswith("/ical/"):
        return "/ical/***.ics" if path.endswith(".ics") else "/ical/***"
    return path


def _route_template(scope: Scope, raw_path: str) -> str:
    """Pfad-Template der Route (begrenzte Kardinalität für Metriken), z. B. ``/api/v1/users/{user_id}``."""
    route = scope.get("route")
    path = getattr(route, "path", None)
    if not path:
        return "<unmatched>"
    if raw_path.startswith("/api/v1/") and not path.startswith("/api/"):
        path = "/api/v1" + path
    return path


class CoreMiddleware:
    """Eine Middleware für alles Querschnittliche (schnell, ohne BaseHTTPMiddleware)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        rid = None
        for key, value in scope.get("headers", []):
            if key == b"x-request-id":
                candidate = value.decode("latin-1")
                if _RID_RE.match(candidate):
                    rid = candidate
                break
        rid = rid or uuid.uuid4().hex
        token = request_id_var.set(rid)
        path: str = scope.get("path", "")
        status = 500
        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = rid
                _security_headers(headers, path)
            await send(message)

        metrics.in_flight += 1
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            metrics.in_flight -= 1
            duration = time.perf_counter() - start
            template = _route_template(scope, path)
            method = scope.get("method", "GET")
            metrics.observe(method, template, status, duration)
            if config.access_log and template not in ("/healthz", "/healthz/ready", "/metrics"):
                client = scope.get("client")
                shown = mask_path(path)
                access_log.info("%s %s %s %.1fms", method, shown, status, duration * 1000,
                                extra={"method": method, "path": shown, "route": template, "status": status,
                                       "duration_ms": round(duration * 1000, 1),
                                       "client": truncate_ip(client[0]) if client else None})
            request_id_var.reset(token)


def _security_headers(headers: MutableHeaders, path: str) -> None:
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "same-origin")
    headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
    headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    headers.setdefault("Content-Security-Policy", csp_for(path))
    if config.is_production or config.cookie_secure:
        headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if path.startswith("/api/") or path.startswith("/ical/"):
        headers.setdefault("Cache-Control", "no-store")
