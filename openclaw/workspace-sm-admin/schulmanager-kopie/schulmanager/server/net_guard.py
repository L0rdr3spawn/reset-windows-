"""Zentrale Zielprüfung für ausgehende Verbindungen, die ein Nutzer oder Admin konfigurieren kann (SSRF-Schutz).

Gilt für: IMAP/SMTP des Postfachs (``mailbridge``), Webhooks (``notify``), OIDC/SSO-Discovery (``sso_providers``),
SMS-Webhook (``sms``), Ferien-Dienst (``holiday_import``) und Lizenzserver (``licensing``).

Regeln
------
* Der Hostname wird **bei jedem Verbindungsaufbau** aufgelöst; **alle** gelieferten Adressen müssen öffentlich sein
  (nicht loopback, privat, link-local, Metadaten, CGNAT, Multicast, reserviert – IPv4 wie IPv6, auch eingebettete
  IPv4-Adressen in ``::ffff:``/6to4/NAT64). Verbunden wird dann direkt mit der geprüften Adresse (kein zweites
  Auflösen → kein DNS-Rebinding); TLS prüft weiter gegen den Hostnamen.
* Erlaubte Ports je Dienst (:data:`PORTS`).
* Webhooks/SSO/SMS: nur ``https`` (``http`` zusätzlich nur in Entwicklung); keine Weiterleitungen.
* Ausnahmeliste für schulinterne Ziele: Umgebungsvariable ``SM_OUTBOUND_ALLOW`` – kommagetrennt Hostnamen, IP-Adressen
  oder Netze (``mail.schule.lokal``, ``10.20.0.5``, ``10.20.0.0/24``), optional mit Port (``keycloak.schule.lokal:8443``).
  Eine Ausnahme hebt nur die Adressprüfung auf; die Ports des Dienstes (oder der angegebene) gelten weiter.
* Fehlermeldungen an Nutzer sind einheitlich (:data:`GENERIC`), Einzelheiten stehen nur im Server-Log.
"""
from __future__ import annotations

import http.client
import ipaddress
import logging
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

log = logging.getLogger("schulmanager.net_guard")

#: Erlaubte Zielports je Dienst
PORTS: dict[str, frozenset[int]] = {
    "imap": frozenset({993}),
    "smtp": frozenset({465, 587, 25}),
    "webhook": frozenset({443, 8443}),
    "oidc": frozenset({443, 8443}),
    "sms": frozenset({443, 8443}),
    "https": frozenset({443}),
    "license": frozenset({443, 8443, 10489}),     # Lizenzserver des Anbieters
}
#: Zusätzlich in Entwicklung (lokale Testserver)
DEV_EXTRA_PORTS: frozenset[int] = frozenset({80, 8080})
#: Dienste mit HTTP(S)-Zielen (Schema wird geprüft)
HTTP_SERVICES = frozenset({"webhook", "oidc", "sms", "https", "license"})

GENERIC = "Dieser Server ist nicht erreichbar oder nicht zulässig."


class BlockedTarget(OSError):
    """Ziel nicht zulässig (Adresse, Port, Schema). ``str(exc)`` ist die allgemeine Meldung für Nutzer."""

    def __init__(self, detail: str = ""):
        super().__init__(GENERIC)
        self.detail = detail


# =========================================================================== Ausnahmeliste
@dataclass(frozen=True)
class _Allow:
    host: str | None = None
    net: Any = None
    port: int | None = None


def parse_allow(raw: str | None) -> tuple[_Allow, ...]:
    out: list[_Allow] = []
    for part in (raw or "").split(","):
        part = part.strip().lower()
        if not part:
            continue
        port = None
        host = part
        if part.startswith("["):                      # [::1]:8443
            end = part.find("]")
            host = part[1:end] if end > 0 else part
            rest = part[end + 1:] if end > 0 else ""
            if rest.startswith(":") and rest[1:].isdigit():
                port = int(rest[1:])
        elif part.count(":") == 1:
            h, _, p = part.partition(":")
            if p.isdigit():
                host, port = h, int(p)
        try:
            out.append(_Allow(net=ipaddress.ip_network(host, strict=False), port=port))
        except ValueError:
            out.append(_Allow(host=host.rstrip("."), port=port))
    return tuple(out)


def _allow_list() -> tuple[_Allow, ...]:
    from .config import config

    return parse_allow(getattr(config, "outbound_allow", ""))


def _excepted(host: str, ip: Any, port: int, allow: Iterable[_Allow]) -> bool:
    for a in allow:
        if a.port is not None and a.port != port:
            continue
        if a.host is not None and a.host == host.lower().rstrip("."):
            return True
        if a.net is not None and ip is not None and ip.version == a.net.version and ip in a.net:
            return True
    return False


# =========================================================================== Adressprüfung
def _embedded_v4(ip: ipaddress.IPv6Address) -> ipaddress.IPv4Address | None:
    if ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    if ip.sixtofour is not None:
        return ip.sixtofour
    if ip.teredo is not None:
        return ip.teredo[1]
    packed = ip.packed
    if packed[:12] == bytes.fromhex("0064ff9b0000000000000000"):       # NAT64 64:ff9b::/96
        return ipaddress.IPv4Address(packed[12:])
    return None


def is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Nur global routbare Unicast-Adressen sind zulässig."""
    if isinstance(ip, ipaddress.IPv6Address):
        inner = _embedded_v4(ip)
        if inner is not None and not is_public_ip(inner):
            return False
    if ip.is_multicast or ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_reserved:
        return False
    return bool(ip.is_global)


def _clean_host(host: str) -> str:
    host = (host or "").strip().strip("[]").rstrip(".")
    if not host or len(host) > 253 or any(c in host for c in " \t\r\n/\\@#?"):
        raise BlockedTarget("ungültiger Hostname")
    return host


def _literal(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        return None


def ports_for(service: str) -> frozenset[int]:
    from .config import config

    ports = PORTS.get(service, PORTS["https"])
    return ports | DEV_EXTRA_PORTS if (config.is_development and service in HTTP_SERVICES) else ports


def check_port(service: str, port: int, host: str = "") -> None:
    if port in ports_for(service):
        return
    if any(a.port == port and (a.host == host.lower().rstrip(".") or a.net is not None) for a in _allow_list()):
        return
    raise BlockedTarget(f"Port {port} für {service} nicht erlaubt")


def resolve_checked(host: str, port: int, service: str) -> list[str]:
    """Löst ``host`` auf und liefert die geprüften Adressen. Wirft :class:`BlockedTarget`, wenn Port oder **eine**
    der Adressen unzulässig ist (außer per Ausnahmeliste)."""
    host = _clean_host(host)
    port = int(port)
    check_port(service, port, host)
    allow = _allow_list()
    lit = _literal(host)
    if lit is not None:
        if not is_public_ip(lit) and not _excepted(host, lit, port, allow):
            raise BlockedTarget(f"Adresse {lit} nicht öffentlich")
        return [str(lit)]
    if host.lower() == "localhost" or host.lower().endswith((".localhost", ".local", ".internal", ".localdomain")):
        if not _excepted(host, None, port, allow):
            raise BlockedTarget("interner Hostname")
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as exc:
        raise BlockedTarget(f"Name nicht auflösbar: {exc}") from None
    addrs: list[str] = []
    for fam, _t, _p, _c, sockaddr in infos:
        if fam not in (socket.AF_INET, socket.AF_INET6):
            continue
        ip = ipaddress.ip_address(sockaddr[0].split("%", 1)[0])
        if not is_public_ip(ip) and not _excepted(host, ip, port, allow):
            raise BlockedTarget(f"{host} löst auf nicht öffentliche Adresse {ip} auf")
        if str(ip) not in addrs:
            addrs.append(str(ip))
    if not addrs:
        raise BlockedTarget("keine Adresse")
    return addrs


def guarded_connect(host: str, port: int, service: str, timeout: float | None = None) -> socket.socket:
    """TCP-Verbindung zu einer **geprüften** Adresse (Auflösen und Verbinden in einem Schritt)."""
    addrs = resolve_checked(host, port, service)
    last: OSError | None = None
    for addr in addrs:
        try:
            if timeout is None:
                return socket.create_connection((addr, int(port)))
            return socket.create_connection((addr, int(port)), timeout)
        except OSError as exc:
            last = exc
    raise last or OSError("keine Verbindung")


# =========================================================================== URLs
def check_url(url: str, service: str, *, resolve: bool = True) -> urllib.parse.SplitResult:
    """Prüft eine URL (Schema, Host, Port, Adressen). Gibt die zerlegte URL zurück."""
    from .config import config

    try:
        parts = urllib.parse.urlsplit(url.strip())
        port = parts.port
    except ValueError:
        raise BlockedTarget("ungültige URL") from None
    if parts.scheme not in ("https", "http") or not parts.hostname:
        raise BlockedTarget("Schema nicht erlaubt")
    if parts.username or parts.password:
        raise BlockedTarget("Zugangsdaten in der URL")
    if parts.scheme == "http" and not config.is_development:
        raise BlockedTarget("nur https erlaubt")
    port = port or (443 if parts.scheme == "https" else 80)
    if resolve:
        resolve_checked(parts.hostname, port, service)
    else:
        check_port(service, port, parts.hostname)
        lit = _literal(parts.hostname)
        if lit is not None and not is_public_ip(lit) and not _excepted(parts.hostname, lit, port, _allow_list()):
            raise BlockedTarget("Adresse nicht öffentlich")
    return parts


def validate_url(url: str, service: str, *, resolve: bool = False) -> str | None:
    """Für Eingabeprüfungen beim Speichern: ``None`` = in Ordnung, sonst deutsche Meldung. Ohne ``resolve`` werden
    Schema, Port und Adress-Literale geprüft; die Namensauflösung folgt bei jeder Verbindung (DNS-Rebinding)."""
    try:
        check_url(url, service, resolve=resolve)
    except BlockedTarget as exc:
        log.info("Ziel abgelehnt (%s): %s – %s", service, url[:200], exc.detail)
        return ("Diese Adresse ist nicht zulässig (nur öffentliche https-Adressen auf den üblichen Ports; "
                "interne Ziele muss die Administration freigeben).")
    return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        raise urllib.error.HTTPError(req.full_url, code, "Weiterleitung nicht erlaubt", headers, fp)


class _GuardedHTTPConnection(http.client.HTTPConnection):
    service = "https"

    def connect(self) -> None:
        self.sock = guarded_connect(self.host, self.port, self.service, self.timeout)
        if self._tunnel_host:  # pragma: no cover - kein Proxy vorgesehen
            self._tunnel()


class _GuardedHTTPSConnection(http.client.HTTPSConnection):
    service = "https"

    def connect(self) -> None:
        sock = guarded_connect(self.host, self.port, self.service, self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _conn_class(base: type, service: str) -> type:
    return type(f"Guarded{base.__name__}_{service}", (base,), {"service": service})


class _HTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, service: str):
        super().__init__()
        self._service = service

    def http_open(self, req):  # noqa: D102
        return self.do_open(_conn_class(_GuardedHTTPConnection, self._service), req)


class _HTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, service: str, context: ssl.SSLContext | None = None):
        self._ctx = context or ssl.create_default_context()
        super().__init__(context=self._ctx)
        self._service = service

    def https_open(self, req):  # noqa: D102
        return self.do_open(_conn_class(_GuardedHTTPSConnection, self._service), req, context=self._ctx)


def build_opener(service: str) -> urllib.request.OpenerDirector:
    opener = urllib.request.OpenerDirector()
    for handler in (urllib.request.UnknownHandler(), _HTTPHandler(service), _HTTPSHandler(service),
                    urllib.request.HTTPDefaultErrorHandler(), _NoRedirect(), urllib.request.HTTPErrorProcessor()):
        opener.add_handler(handler)
    return opener


def urlopen(req: urllib.request.Request | str, service: str, timeout: float = 10.0):
    """Wie ``urllib.request.urlopen``, aber mit Zielprüfung, geprüfter Adresse und ohne Weiterleitungen."""
    url = req.full_url if isinstance(req, urllib.request.Request) else req
    check_url(url, service, resolve=False)          # Schema/Port früh ablehnen; Adressen prüft ``connect``
    return build_opener(service).open(req, timeout=timeout)


# =========================================================================== IMAP / SMTP
def check_mail_host(host: str, port: int, service: str) -> None:
    """Vorabprüfung beim Eintragen eines Mailservers (Meldung an Nutzer: :data:`GENERIC`)."""
    resolve_checked(host, port, service)


def imap_ssl_class():
    import imaplib

    class GuardedIMAP4_SSL(imaplib.IMAP4_SSL):
        def _create_socket(self, timeout):  # noqa: D102
            sock = guarded_connect(self.host, self.port, "imap", timeout)
            return self.ssl_context.wrap_socket(sock, server_hostname=self.host)

    return GuardedIMAP4_SSL


def smtp_classes():
    import smtplib

    class GuardedSMTP(smtplib.SMTP):
        def _get_socket(self, host, port, timeout):  # noqa: D102
            return guarded_connect(host, port, "smtp", timeout)

    class GuardedSMTP_SSL(smtplib.SMTP_SSL):
        def _get_socket(self, host, port, timeout):  # noqa: D102
            sock = guarded_connect(host, port, "smtp", timeout)
            return self.context.wrap_socket(sock, server_hostname=self._host)

    return GuardedSMTP, GuardedSMTP_SSL
