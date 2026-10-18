"""Logging: JSON-Zeilen (Produktion) oder lesbarer Text (Entwicklung), Request-ID im Kontext."""
from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone

from .config import config

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime", "taskName",
                                                                             "color_message"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = request_id_var.get()
        if rid:
            out["request_id"] = rid
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                out[key] = value if isinstance(value, (str, int, float, bool, type(None), list, dict)) else str(value)
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        rid = request_id_var.get()
        return f"{text} [{rid}]" if rid else text


def truncate_ip(ip: str | None) -> str | None:
    """IP für Protokolle kürzen (Datensparsamkeit): IPv4 → /24 (``203.0.113.0``), IPv6 → /48 (``2001:db8:1::``).
    Kein IP-Format (Unix-Socket, ``testclient``) → ``None``."""
    if not ip:
        return None
    import ipaddress

    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return None
    if addr.version == 6 and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    prefix = 24 if addr.version == 4 else 48
    return str(ipaddress.ip_network(f"{addr}/{prefix}", strict=False).network_address)


_HANDLER_FLAG = "_schulmanager_handler"


def setup_logging() -> None:
    """Richtet das Root-Logging ein (idempotent; ersetzt nur den eigenen Handler)."""
    root = logging.getLogger()
    for h in list(root.handlers):
        if getattr(h, _HANDLER_FLAG, False):
            root.removeHandler(h)
    handler = logging.StreamHandler(sys.stderr)
    setattr(handler, _HANDLER_FLAG, True)
    handler.setFormatter(JsonFormatter() if config.log_format == "json" else TextFormatter())
    level = getattr(logging, config.log_level, logging.INFO)
    logging.getLogger("schulmanager").setLevel(level)
    # Unter pytest hängt ein Capture-Handler am Root – dann keinen zweiten Ausgabe-Handler hinzufügen
    if not any(type(h).__name__ == "LogCaptureHandler" for h in root.handlers):
        root.addHandler(handler)
        if root.level > level or root.level == logging.WARNING:
            root.setLevel(level)
    if level > logging.DEBUG:
        logging.getLogger("alembic").setLevel(logging.WARNING)
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        if config.log_format == "json":
            lg.handlers = []
            lg.propagate = True
    if config.log_format == "json":
        logging.getLogger("uvicorn.access").disabled = True  # eigenes Access-Log (schulmanager.access)
