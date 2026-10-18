"""Vertrauenswürdige Reverse-Proxys (Sicherheitsprüfung S-10).

uvicorn läuft mit ``--no-proxy-headers``; ``X-Forwarded-*`` wertet erst diese Middleware aus – und nur, wenn
``SM_TRUST_PROXY=1`` gilt **und** die unmittelbare Gegenstelle (TCP-Peer) in ``SM_TRUSTED_PROXIES`` liegt
(IP-Adressen oder Netze, kommagetrennt; Standard ohne Angabe: nur Loopback ``127.0.0.1``/``::1``).

* Vertrauenswürdiger Peer: ``scope["client"]`` wird zur Client-IP aus ``X-Forwarded-For`` (``SM_PROXY_COUNT``
  Einträge von rechts), ``scope["scheme"]`` aus ``X-Forwarded-Proto``.
* Anderer Peer (z. B. direkt veröffentlichter Container): alle ``X-Forwarded-*``/``X-Real-IP``-Köpfe werden
  entfernt, damit weder die IP-Sperre noch IP-Allowlists noch ``Secure``-Cookies gefälscht werden können.
* Peer ohne IP-Adresse (Unix-Socket, Test-Client): gilt als vertrauenswürdig – dort gibt es keinen Netzwerk-Peer.
"""
from __future__ import annotations

import ipaddress
import logging

from .config import config

log = logging.getLogger("schulmanager.proxy")

_STRIP = {b"x-forwarded-for", b"x-forwarded-proto", b"x-forwarded-host", b"x-forwarded-port", b"x-real-ip",
          b"forwarded"}
_DEFAULT = ("127.0.0.1", "::1")


def parse_trusted(spec: str | None) -> tuple[list, bool]:
    """``"10.0.0.0/8, 127.0.0.1"`` → (Netze, ``alle``). ``*`` = jede Adresse (nur ausdrücklich, unsicher)."""
    nets: list = []
    allow_all = False
    for part in (spec or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if part == "*":
            allow_all = True
            continue
        try:
            nets.append(ipaddress.ip_network(part, strict=False))
        except ValueError:
            log.warning("SM_TRUSTED_PROXIES: %r ist keine IP-Adresse/kein Netz – ignoriert", part)
    return nets, allow_all


def peer_is_trusted(peer: str | None, nets: list, allow_all: bool) -> bool:
    if allow_all:
        return True
    try:
        addr = ipaddress.ip_address((peer or "").strip())
    except ValueError:
        return True          # kein IP-Peer (Unix-Socket, Test-Client)
    if addr.version == 6 and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return any(addr in n for n in nets)


class TrustedProxyMiddleware:
    def __init__(self, app):
        self.app = app
        spec = config.trusted_proxies or ",".join(_DEFAULT)
        self.nets, self.allow_all = parse_trusted(spec)
        if config.trust_proxy and self.allow_all:
            log.warning("SM_TRUSTED_PROXIES=* : X-Forwarded-* wird von JEDER Adresse geglaubt – die App darf dann "
                        "nie direkt erreichbar sein (S-10).")

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket") and config.trust_proxy:
            client = scope.get("client")
            if peer_is_trusted(client[0] if client else None, self.nets, self.allow_all):
                scope = self._apply(scope)
            else:
                scope = dict(scope)
                scope["headers"] = [(k, v) for k, v in scope["headers"] if k.lower() not in _STRIP]
        await self.app(scope, receive, send)

    @staticmethod
    def _apply(scope):
        headers = {k.lower(): v for k, v in scope["headers"]}
        scope = dict(scope)
        fwd = headers.get(b"x-forwarded-for", b"").decode("latin-1")
        parts = [p.strip() for p in fwd.split(",") if p.strip()]
        if parts:
            ip = parts[-min(config.proxy_count, len(parts))][:64]
            scope["client"] = (ip, 0)
        proto = headers.get(b"x-forwarded-proto", b"").decode("latin-1").split(",")[0].strip().lower()
        if proto in ("http", "https", "ws", "wss"):
            scope["scheme"] = (proto.replace("http", "ws") if scope["type"] == "websocket" and proto in ("http", "https")
                               else proto)
        return scope
