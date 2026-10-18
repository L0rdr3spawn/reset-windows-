"""Verbindung zum Update-Server des Anbieters (derselbe Server wie die Lizenzprüfung).

Zwei Aufrufe: ``poll`` (signierte Antwort, Nonce) und ``download`` (Abbild-Datei, nur mit Schlüssel + Instanz-ID).
Der Transport ist austauschbar (Tests nutzen einen In-Process-Lizenzserver).
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol


class TransportError(Exception):
    pass


class Transport(Protocol):
    def post_json(self, url: str, body: dict, timeout: float) -> dict: ...

    def download(self, url: str, headers: dict[str, str], dest: Path, timeout: float) -> tuple[str, int]:
        """Lädt nach ``dest``; gibt ``(sha256_hex, Größe)`` zurück."""
        ...


class UrllibTransport:
    def __init__(self, *, allow_insecure: bool = False) -> None:
        self.allow_insecure = allow_insecure

    def _check(self, url: str) -> None:
        if url.startswith("https://"):
            return
        if self.allow_insecure and url.startswith(("http://127.0.0.1", "http://localhost")):
            return
        raise TransportError("Nur HTTPS ist erlaubt.")

    def post_json(self, url: str, body: dict, timeout: float) -> dict:
        self._check(url)
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": "Schulpuls-Updater"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:                       # noqa: S310 – oben geprüft
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
            raise TransportError(f"Anbieter nicht erreichbar: {str(exc)[:150]}") from exc

    def download(self, url: str, headers: dict[str, str], dest: Path, timeout: float) -> tuple[str, int]:
        self._check(url)
        req = urllib.request.Request(url, headers={**headers, "User-Agent": "Schulpuls-Updater"})
        h, size = hashlib.sha256(), 0
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r, dest.open("wb") as f:  # noqa: S310
                for chunk in iter(lambda: r.read(1 << 20), b""):
                    f.write(chunk)
                    h.update(chunk)
                    size += len(chunk)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            dest.unlink(missing_ok=True)
            raise TransportError(f"Download fehlgeschlagen: {str(exc)[:150]}") from exc
        return h.hexdigest(), size


class VendorClient:
    def __init__(self, base_url: str, transport: Transport, *, timeout: float = 20.0) -> None:
        self.base = base_url.rstrip("/")
        self.transport = transport
        self.timeout = timeout

    def poll(self, body: dict) -> dict:
        return self.transport.post_json(f"{self.base}/api/v1/updates/poll", body, self.timeout)

    def download(self, version: str, key: str, instance_id: str, dest: Path) -> tuple[str, int]:
        return self.transport.download(f"{self.base}/api/v1/updates/download/{version}",
                                       {"X-License-Key": key, "X-Instance-Id": instance_id}, dest, 600.0)
