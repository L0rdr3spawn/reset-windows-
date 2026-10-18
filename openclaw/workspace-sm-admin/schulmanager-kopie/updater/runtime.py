"""Austauschbare „Laufzeit“ des Update-Agenten: Docker (Produktion) oder Fake (Tests, Simulation).

Der Agent ruft nur diese kleine Schnittstelle auf. Die Docker-Variante nutzt die ``docker``-Befehlszeile gegen den
Docker-Socket des Hosts; sie startet ausschließlich den Dienst ``app`` der Compose-Datei der Schule neu.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Health:
    ok: bool
    version: str = ""
    detail: str = ""


class RuntimeError_(Exception):
    """Fehler der Laufzeit (Docker-Befehl fehlgeschlagen o. ä.)."""


class Runtime:
    """Schnittstelle. Alle Methoden werfen :class:`RuntimeError_` bei Fehlern."""

    def current_image(self) -> str:
        raise NotImplementedError

    def load_image(self, path: Path, version: str) -> str:
        """Image-Datei laden; gibt die lokale Referenz zurück (z. B. ``schulpuls-app:1.4.0``)."""
        raise NotImplementedError

    def pull_image(self, image: str, digest: str, version: str) -> str:
        """Abbild aus der Registry **per Digest** holen; gibt die lokale Referenz zurück."""
        raise NotImplementedError

    def backup(self, label: str) -> str:
        """Sicherung (Datenbank + Dateien) anlegen; gibt eine Kennung zurück."""
        raise NotImplementedError

    def apply_image(self, ref: str) -> None:
        """Dienst ``app`` mit diesem Abbild neu erstellen/starten (die App migriert beim Start)."""
        raise NotImplementedError

    def health(self) -> Health:
        raise NotImplementedError

    def restore(self, backup_id: str) -> None:
        raise NotImplementedError

    def stop_app(self) -> None:
        raise NotImplementedError

    def start_app(self) -> None:
        raise NotImplementedError


# --------------------------------------------------------------------------- Fake
@dataclass
class FakeRuntime(Runtime):
    """Simuliert Docker für Tests: Abbilder haben eine Version und ein Verhalten (gesund / ungesund / Migration)."""

    image: str = "schulpuls-app:1.0.0"
    running: bool = True
    schema: str = "1.0.0"                                  # Version des Datenbankschemas
    images: dict[str, dict] = field(default_factory=dict)  # ref -> {"version", "healthy", "migrates_to", "works_with"}
    calls: list[str] = field(default_factory=list)
    fail_on: set[str] = field(default_factory=set)         # Methodennamen, die einen Fehler werfen
    backups: dict[str, str] = field(default_factory=dict)  # id -> Schema zum Zeitpunkt der Sicherung
    health_script: list[bool] | None = None                # feste Antworten für health() (Ablauf-Tests)
    loaded: list[str] = field(default_factory=list)

    def _do(self, name: str) -> None:
        self.calls.append(name)
        if name in self.fail_on:
            raise RuntimeError_(f"{name} simuliert fehlgeschlagen")

    def _version(self) -> str:
        return self.images.get(self.image, {"version": self.image.rsplit(":", 1)[-1]})["version"]

    def current_image(self) -> str:
        return self.image

    def load_image(self, path: Path, version: str) -> str:
        self._do("load_image")
        ref = f"schulpuls-app:{version}"
        self.images.setdefault(ref, {"version": version, "healthy": True})
        self.loaded.append(ref)
        return ref

    def pull_image(self, image: str, digest: str, version: str) -> str:
        self._do("pull_image")
        ref = f"schulpuls-app:{version}"
        self.images.setdefault(ref, {"version": version, "healthy": True})
        return ref

    def backup(self, label: str) -> str:
        self._do("backup")
        bid = f"backup-{label}"
        self.backups[bid] = self.schema
        return bid

    def apply_image(self, ref: str) -> None:
        self._do("apply_image")
        self.image, self.running = ref, True
        spec = self.images.get(ref, {})
        if spec.get("migrates_to"):
            self.schema = spec["migrates_to"]               # die App migriert beim Start

    def health(self) -> Health:
        self.calls.append("health")
        if self.health_script:
            ok = self.health_script.pop(0) if len(self.health_script) > 1 else self.health_script[0]
            return Health(ok, self._version(), "" if ok else "simuliert ungesund")
        if not self.running:
            return Health(False, "", "App gestoppt")
        spec = self.images.get(self.image, {"healthy": True})
        works = spec.get("works_with")                       # Schemata, mit denen dieses Abbild laufen kann
        if works is not None and self.schema not in works:
            return Health(False, self._version(), "Schema passt nicht")
        ok = bool(spec.get("healthy", True))
        return Health(ok, self._version(), "" if ok else "ungesund")

    def restore(self, backup_id: str) -> None:
        self._do("restore")
        self.schema = self.backups[backup_id]

    def stop_app(self) -> None:
        self._do("stop_app")
        self.running = False

    def start_app(self) -> None:
        self._do("start_app")
        self.running = True


# --------------------------------------------------------------------------- Docker
class DockerRuntime(Runtime):
    """Docker-Compose-Betrieb der Schule.

    ``compose_dir``: Ordner mit ``docker-compose.yml`` und ``.env`` (im Agent-Container unter **demselben Pfad** wie auf dem
    Host eingebunden, damit relative Pfade der Compose-Datei stimmen). Das gewünschte Abbild steht in
    ``update.env`` (``SM_IMAGE=…``), die Compose-Datei liest es über ``${SM_IMAGE}``.
    """

    def __init__(self, compose_dir: Path, *, health_url: str = "http://app:8000/healthz", service: str = "app",
                 backup_service: str = "backup", project: str = "", timeout: int = 900) -> None:
        self.dir, self.health_url, self.service = Path(compose_dir), health_url, service
        self.backup_service, self.project, self.timeout = backup_service, project, timeout

    # ------------------------------------------------------------ Hilfen
    def _run(self, *args: str, timeout: int | None = None) -> str:
        try:
            done = subprocess.run(list(args), cwd=self.dir, capture_output=True, text=True,
                                  timeout=timeout or self.timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError_(f"{args[0]} {args[1] if len(args) > 1 else ''}: {exc}") from exc
        if done.returncode != 0:
            raise RuntimeError_(f"{' '.join(args[:3])} fehlgeschlagen: {(done.stderr or done.stdout)[-400:]}")
        return done.stdout

    def _compose(self, *args: str) -> str:
        cmd = ["docker", "compose"]
        if self.project:
            cmd += ["-p", self.project]
        env_files = [self.dir / ".env", self.dir / "update.env"]
        for f in env_files:
            if f.is_file():
                cmd += ["--env-file", str(f)]
        return self._run(*cmd, *args)

    # ------------------------------------------------------------ Schnittstelle
    def current_image(self) -> str:
        cid = self._compose("ps", "-q", self.service).strip().splitlines()
        if not cid:
            raise RuntimeError_("Der Dienst app läuft nicht")
        return self._run("docker", "inspect", "--format", "{{.Config.Image}}", cid[0]).strip()

    def load_image(self, path: Path, version: str) -> str:
        out = self._run("docker", "load", "-i", str(path))
        m = re.search(r"Loaded image(?: ID)?: (\S+)", out)
        if not m:
            raise RuntimeError_("docker load meldet kein Abbild")
        ref = f"schulpuls-app:{version}"
        self._run("docker", "tag", m.group(1), ref)
        return ref

    def pull_image(self, image: str, digest: str, version: str) -> str:
        pinned = f"{image.split('@')[0].split(':')[0]}@{digest}"      # nur per Digest, nie per Tag
        self._run("docker", "pull", pinned)
        ref = f"schulpuls-app:{version}"
        self._run("docker", "tag", pinned, ref)
        return ref

    def backup(self, label: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]", "-", label)[:40]
        self._compose("exec", "-T", self.backup_service, "backup.sh", "--label", safe)
        out = self._compose("exec", "-T", self.backup_service, "sh", "-c",
                            f"ls -t /backups/manual/*_{safe}.* 2>/dev/null | head -20")
        files = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if not files:
            raise RuntimeError_("Die Sicherung wurde nicht gefunden")
        return json.dumps(files)

    def apply_image(self, ref: str) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9._/:@-]{0,260}", ref):
            raise RuntimeError_("Ungültige Abbild-Angabe")
        tmp = self.dir / "update.env.tmp"
        tmp.write_text(f"SM_IMAGE={ref}\n", encoding="utf-8")
        tmp.replace(self.dir / "update.env")
        self._compose("up", "-d", "--no-deps", "--no-build", "--force-recreate", self.service)

    def health(self) -> Health:
        try:
            with urllib.request.urlopen(self.health_url, timeout=5) as r:        # noqa: S310 – feste, interne Adresse
                body = json.loads(r.read().decode("utf-8"))
            ok = r.status == 200 and body.get("status") == "ok" and body.get("db") == "ok" and body.get("started", True)
            # Anmeldeseite (Frontend) muss ausgeliefert werden
            base = self.health_url.rsplit("/healthz", 1)[0]
            with urllib.request.urlopen(base + "/", timeout=5) as r2:            # noqa: S310
                page_ok = r2.status == 200
            return Health(bool(ok and page_ok), str(body.get("version", "")), "" if ok and page_ok else "Seite nicht erreichbar")
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
            return Health(False, "", str(exc)[:200])

    def stop_app(self) -> None:
        self._compose("stop", self.service)

    def start_app(self) -> None:
        self._compose("start", self.service)

    def restore(self, backup_id: str) -> None:
        files = json.loads(backup_id)
        self._compose("stop", self.service)
        for f in files:                                  # Datenbank (dump/db.gz) und Dateien (tar.gz) der Sicherung
            self._compose("exec", "-T", self.backup_service, "restore.sh", "--yes", "--no-safety-backup", f)
        self._compose("start", self.service)
