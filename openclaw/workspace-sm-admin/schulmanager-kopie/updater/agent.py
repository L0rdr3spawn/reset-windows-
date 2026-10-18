"""Update-Agent einer Schule (ein Agent je Server).

Er fragt den Anbieter regelmäßig, ob für **diesen Server** ein Update freigegeben ist, und führt nur eine einzige Art von
Auftrag aus: „Version X installieren“. Befehle, Skripte oder Adressen aus der Antwort werden nie ausgeführt.

Ablauf einer Installation (``_install``): Last wegnehmen (drain) → Sicherung → neues Abbild starten (die App migriert beim Start)
→ Gesundheitsprüfung (``/healthz``, Version, Startseite) → bei Erfolg wieder in den Lastausgleich; bei Fehler das alte Abbild
zurück und, falls nötig und gefahrlos, die Sicherung einspielen. Jeder Schritt wird dem Anbieter gemeldet, auch damit er bei
mehreren Servern der Schule immer nur so viele gleichzeitig freigibt, wie vereinbart (Schloss beim Anbieter).

Dateien (Datenordner der App, gemeinsam mit dem App-Container):

* ``license.json`` / ``license_state.json`` – nur gelesen (Schlüssel, Instanz-ID).
* ``updater/plan.json`` – von der App geschrieben (Verschieben, „nur manuell“, „Jetzt installieren“).
* ``updater/status.json`` – vom Agenten geschrieben (Anzeige unter ``/betrieb``).
* ``drain-<node>.flag`` – vom Agenten geschrieben; die App meldet dann ``/healthz/ready`` mit 503, der Lastausgleich nimmt
  den Server heraus.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import shutil
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from . import policy
from .client import TransportError, VendorClient
from .runtime import Health, Runtime
from .runtime import RuntimeError_ as RuntimeFailure

log = logging.getLogger("updater")

BUSY = ("draining", "backing_up", "updating", "verifying", "held")
STICKY = ("rolled_back", "error")


@dataclass
class Config:
    vendor_url: str
    pubkey: str
    data_dir: Path
    state_dir: Path
    node: str = "main"
    node_id: str = ""
    mode: str = "auto"                  # auto | manual (Wahl der Schule)
    drain_seconds: float = 20.0
    health_timeout: float = 300.0
    health_interval: float = 5.0
    health_ok_required: int = 3
    min_free_mb: int = 2048
    allowed_registry: str = ""
    max_postpone_days: int = 7
    keep_downloads: int = 1


@dataclass
class Step:
    """Ergebnis eines ``tick`` (für Tests und Protokoll)."""

    action: str = "none"
    state: str = "idle"
    detail: str = ""


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        d = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    except ValueError:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


class Agent:
    def __init__(self, cfg: Config, client: VendorClient, runtime: Runtime, *,
                 clock: Callable[[], datetime] | None = None, sleep: Callable[[float], None] = time.sleep) -> None:
        self.cfg, self.client, self.rt = cfg, client, runtime
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sleep = sleep
        self.pub = policy.load_pubkey(cfg.pubkey)
        self.state_path = cfg.state_dir / "agent.json"
        self.st: dict[str, Any] = {"highest": "", "state": "idle", "target": "", "failed": {}, "prepared": None,
                                   "in_progress": None, "retry_seq": 0, "postponed": {}, "consumed": "", "log": [],
                                   "fingerprint": policy.fingerprint(cfg.pubkey)}
        self.st.update(_read_json(self.state_path))
        if self.st.get("fingerprint") != policy.fingerprint(cfg.pubkey):
            raise SystemExit("Der Anbieter-Schlüssel hat sich gegenüber dem gemerkten geändert – Agent hält an "
                             "(Schlüssel-Pinning). Bewusster Wechsel: agent.json im Zustandsordner löschen.")
        self.offered: dict | None = None
        self.window: dict | None = None
        self.last_poll: str = ""
        self.last_ok: str = ""
        self.last_error: str = ""
        self.announce: str = ""
        self.urgent = False
        self.options: dict = {}

    # ------------------------------------------------------------------ Zustand / Protokoll
    def _save(self) -> None:
        _write_json(self.state_path, self.st)

    def _log(self, text: str) -> None:
        log.info(text)
        self.st["log"] = (self.st.get("log", []) + [{"ts": _iso(self.clock()), "text": text[:300]}])[-60:]
        self._save()

    @property
    def node_id(self) -> str:
        return self.cfg.node_id or self.cfg.node

    def _identity(self) -> tuple[str, str] | None:
        key = str(_read_json(self.cfg.data_dir / "license.json").get("key") or "")
        inst = str(_read_json(self.cfg.data_dir / "license_state.json").get("instance_id") or "")
        return (key, inst) if key and inst else None

    def _plan(self) -> dict:
        return _read_json(self.cfg.data_dir / "updater" / "plan.json")

    def _write_status(self, version: str) -> None:
        plan = self._plan()
        offered = self.offered
        used = self.st.get("postponed", {})
        can_postpone = bool(offered) and not self.urgent and offered["version"] not in used
        _write_json(self.cfg.data_dir / "updater" / "status.json", {
            "node": self.cfg.node, "version": version, "state": self.st["state"], "detail": self.st.get("detail", ""),
            "offered": offered, "window": self.window, "announce": self.announce, "urgent": self.urgent,
            "prepared": (self.st.get("prepared") or {}).get("version"), "last_poll_at": self.last_poll,
            "last_ok_at": self.last_ok, "last_error": self.last_error, "mode": self._mode(plan),
            "postponed_until": (used.get(offered["version"]) if offered else None), "can_postpone": can_postpone,
            "failed": self.st.get("failed", {}), **self.options, "highest_installed": self.st.get("highest", ""),
            "log": self.st.get("log", [])[-30:], "updated_at": _iso(self.clock()),
        })

    def _mode(self, plan: dict) -> str:
        return "manual" if "manual" in (self.cfg.mode, plan.get("mode")) else "auto"

    # ------------------------------------------------------------------ Abfrage
    def _body(self, ident: tuple[str, str], version: str, plan: dict, *, state: str | None = None,
              detail: str = "") -> tuple[dict, str]:
        nonce = secrets.token_hex(16)
        offered = self.offered["version"] if self.offered else ""
        target = self.st.get("target") or (self.st.get("prepared") or {}).get("version") or offered
        body: dict[str, Any] = {
            "key": ident[0], "instance_id": ident[1], "node": self.cfg.node, "version": version[:40],
            "state": state or self.st["state"], "detail": (detail or self.st.get("detail", ""))[:300],
            "target_version": target or "", "health_ok": self.st["state"] not in STICKY, "mode": self._mode(plan),
            "install_now": False, "postponed_until": None, "nonce": nonce,
            "strategy": plan.get("strategy") if plan.get("strategy") in ("simultaneous", "rolling") else None}
        req = plan.get("install_now") or {}
        if req.get("id") and req["id"] != self.st.get("consumed") and self._mode(plan) == "manual":
            body["install_now"] = True
        if self._mode(plan) == "auto" and req.get("id") and req["id"] != self.st.get("consumed"):
            body["install_now"] = True                       # „Jetzt installieren“ gilt auch im Automatikbetrieb
        until = self._postpone_until(plan)
        if until:
            body["postponed_until"] = _iso(until)
        return body, nonce

    def _postpone_until(self, plan: dict) -> datetime | None:
        """Verschiebung durch die Schule: höchstens ``max_postpone_days`` Tage und nur **einmal** je Version."""
        req = plan.get("postpone") or {}
        version, until = str(req.get("version", "")), _parse(req.get("until"))
        used = self.st.setdefault("postponed", {})
        if version and version in used:
            d = _parse(used[version])
            return d if d and d > self.clock() else None
        if not version or until is None or self.urgent:
            return None
        if self.offered is None or self.offered["version"] != version:
            return None
        until = min(until, self.clock() + timedelta(days=self.cfg.max_postpone_days))
        if until <= self.clock():
            return None
        used[version] = _iso(until)
        self._save()
        self._log(f"Update {version} von der Administration bis {_iso(until)} verschoben")
        return until

    def _ask(self, ident: tuple[str, str], version: str, plan: dict, *, state: str | None = None,
             detail: str = "") -> dict | None:
        """Fragt den Anbieter; gibt das **geprüfte** Ergebnis oder ``None`` zurück."""
        body, nonce = self._body(ident, version, plan, state=state, detail=detail)
        self.last_poll = _iso(self.clock())
        try:
            resp = self.client.poll(body)
        except TransportError as exc:
            self.last_error = str(exc)
            return None
        result, sig = resp.get("result"), str(resp.get("signature") or "")
        if not isinstance(result, dict) or not policy.verify_signed(self.pub, result, sig):
            self.last_error = "Antwort des Anbieters nicht korrekt signiert – ignoriert"
            return None
        if result.get("nonce") != nonce or result.get("instance_id") != ident[1] or result.get("node") != self.cfg.node:
            self.last_error = "Antwort passt nicht zur Anfrage – ignoriert"
            return None
        self.last_error, self.last_ok = "", self.last_poll
        if body["install_now"] and result.get("action") == "install":
            self.st["consumed"] = (plan.get("install_now") or {}).get("id", "")
        return result

    def _set(self, state: str, detail: str = "", ident: tuple[str, str] | None = None, version: str = "") -> None:
        self.st["state"], self.st["detail"] = state, detail
        self._save()
        if ident:                                           # Zustandswechsel sofort melden (wichtig für das Schloss)
            self._ask(ident, version, self._plan(), state=state, detail=detail)

    # ------------------------------------------------------------------ Hauptschritt
    def tick(self) -> Step:
        ident = self._identity()
        version = self._running_version()
        if ident is None:
            self.st["state"], self.st["detail"] = "idle", "Keine Lizenz eingetragen"
            self._write_status(version)
            return Step("none", "idle", "Keine Lizenz")
        self.recover(ident, version)
        plan = self._plan()
        result = self._ask(ident, version, plan)
        if result is None:
            self._write_status(version)
            return Step("none", self.st["state"], self.last_error)
        step = self._handle(result, ident, version, plan)
        self._write_status(self._running_version() or version)
        return step

    def _running_version(self) -> str:
        try:
            h = self.rt.health()
            if h.version:
                self.st["last_version"] = h.version
            return h.version or self.st.get("last_version", "")
        except RuntimeFailure:
            return self.st.get("last_version", "")

    def _handle(self, res: dict, ident: tuple[str, str], version: str, plan: dict) -> Step:
        seq = int(res.get("retry_seq") or 0)
        if seq > int(self.st.get("retry_seq", 0)):          # der Anbieter hat „Erneut versuchen“ gedrückt
            self.st.update(retry_seq=seq, failed={}, state="idle", detail="")
            self.st["target"] = ""
            self._log("Anbieter hat den Fehlerzustand zurückgesetzt – neuer Versuch möglich")
        action = res.get("action", "none")
        self.announce, self.urgent = str(res.get("announce") or ""), bool(res.get("urgent"))
        self.options = {"strategy": res.get("strategy"), "may_choose_strategy": bool(res.get("may_choose_strategy")),
                        "contract_manual": bool(res.get("contract_manual")), "nodes": int(res.get("nodes") or 1)}
        self.window = res.get("window")
        rel = res.get("release")
        if action == "none" or not rel:
            self.offered = None
            if self.st["state"] in ("ready", "waiting", "downloading", "manual", "postponed", "held"):
                if self.st["state"] == "held":
                    self._release_hold()
                self.st["state"], self.st["detail"] = "idle", ""
                self._save()
            return Step("none", self.st["state"], str(res.get("reason") or ""))
        manifest, sig = rel.get("manifest"), str(rel.get("signature") or "")
        verdict = policy.check_release(manifest, sig, self.pub, installed=version,
                                       highest_installed=str(self.st.get("highest", "")),
                                       allowed_registry=self.cfg.allowed_registry)
        if not verdict.ok:
            self.offered = None
            self._log(f"Angebot abgelehnt: {verdict.reason}")
            return Step("none", self.st["state"], verdict.reason)
        target = manifest["version"]
        if target in self.st.get("failed", {}):
            self.offered = None
            return Step("none", self.st["state"], "Für diese Version ist bereits ein Fehler gemeldet")
        self.offered = {"version": target, "notes": manifest.get("notes", ""), "urgent": self.urgent,
                        "migration": manifest.get("migration"), "channel": manifest.get("channel")}
        if action == "offer":
            self._set("manual", "Update verfügbar – wartet auf Freigabe durch die Administration")
            return Step("offer", "manual", str(res.get("reason") or ""))
        if action == "prepare":
            until = self._postpone_until(plan)
            if res.get("reason") == "Von der Schule verschoben" or until:
                self._prepare(ident, version, manifest, state_after="postponed")
                return Step("prepare", "postponed", str(res.get("reason") or ""))
            self._prepare(ident, version, manifest, state_after="ready")
            return Step("prepare", self.st["state"], str(res.get("reason") or ""))
        if action == "hold":
            self._prepare(ident, version, manifest, state_after="ready")
            self._hold(ident, version)
            return Step("hold", "held", str(res.get("reason") or ""))
        if action == "install":
            self._prepare(ident, version, manifest, state_after="ready")
            if self.st["state"] == "ready" or self.st["state"] == "held":
                self._install(ident, version, manifest, res)
            return Step("install", self.st["state"], str(res.get("reason") or ""))
        return Step("none", self.st["state"], "unbekannte Aktion ignoriert")

    # ------------------------------------------------------------------ Vorbereiten (Download + Prüfung)
    def _prepare(self, ident: tuple[str, str], version: str, manifest: dict, *, state_after: str) -> None:
        target = manifest["version"]
        prep = self.st.get("prepared")
        if prep and prep.get("version") == target:
            if self.st["state"] not in BUSY and self.st["state"] != state_after:
                self._set(state_after, f"Version {target} liegt bereit", ident, version)
            return
        self._set("downloading", f"Lade Version {target}", ident, version)
        dist = manifest["dist"]
        try:
            if dist["type"] == "download":
                dest_dir = self.cfg.state_dir / "downloads"
                dest_dir.mkdir(parents=True, exist_ok=True)
                free_mb = shutil.disk_usage(dest_dir).free // (1 << 20)
                if free_mb < max(self.cfg.min_free_mb, 2 * dist["size"] // (1 << 20)):
                    raise RuntimeFailure(f"Zu wenig freier Speicher ({free_mb} MB)")
                dest = dest_dir / f"schulpuls-{target}.tar.part"
                sha, size = self.client.download(target, ident[0], ident[1], dest)
                if sha != dist["sha256"] or size != dist["size"]:
                    dest.unlink(missing_ok=True)
                    raise RuntimeFailure("Prüfsumme oder Größe der Datei stimmt nicht – Download verworfen")
                final = dest_dir / f"schulpuls-{target}.tar"
                dest.replace(final)
                ref = self.rt.load_image(final, target)
                self._cleanup_downloads(keep=final)
            else:
                ref = self.rt.pull_image(dist["image"], dist["digest"], target)
        except (RuntimeFailure, TransportError) as exc:
            self.st["prepared"] = None
            self._log(f"Vorbereitung von {target} fehlgeschlagen: {exc}")
            self._set("idle", f"Vorbereitung fehlgeschlagen: {exc}"[:280])
            return
        self.st["prepared"] = {"version": target, "ref": ref}
        self._log(f"Version {target} geladen und geprüft")
        self._set(state_after, f"Version {target} liegt bereit", ident, version)

    def _cleanup_downloads(self, keep: Path) -> None:
        for f in (self.cfg.state_dir / "downloads").glob("schulpuls-*.tar*"):
            if f != keep:
                f.unlink(missing_ok=True)

    # ------------------------------------------------------------------ Drain / Halten
    def _drain(self, on: bool) -> None:
        flag = self.cfg.data_dir / f"drain-{self.node_id}.flag"
        if on:
            flag.parent.mkdir(parents=True, exist_ok=True)
            flag.write_text(_iso(self.clock()), encoding="utf-8")
        else:
            flag.unlink(missing_ok=True)

    def _hold(self, ident: tuple[str, str], version: str) -> None:
        if self.st["state"] == "held":
            return
        self._drain(True)
        self.sleep(self.cfg.drain_seconds)
        try:
            self.rt.stop_app()
        except RuntimeFailure as exc:
            self._drain(False)
            self._set("error", f"Anhalten fehlgeschlagen: {exc}"[:280], ident, version)
            return
        self._set("held", "Wartungsfenster: angehalten, bis der erste Server aktualisiert ist", ident, version)

    def _release_hold(self) -> None:
        try:
            self.rt.start_app()
        finally:
            self._drain(False)

    # ------------------------------------------------------------------ Installation
    def _install(self, ident: tuple[str, str], version: str, manifest: dict, res: dict) -> None:
        target, prep = manifest["version"], self.st["prepared"]
        mig = manifest["migration"]
        nodes, strategy = int(res.get("nodes") or 1), str(res.get("strategy") or "single")
        allow_restore = nodes <= 1 or strategy == "maintenance"
        was_held = self.st["state"] == "held"
        try:
            prev = self.rt.current_image()
        except RuntimeFailure:
            prev = self.st.get("prev_image", "")
        self.st["in_progress"] = {"version": target, "prev_image": prev, "prev_version": version, "ref": prep["ref"], "backup": None,
                                  "migration": mig, "allow_restore": allow_restore, "started": _iso(self.clock())}
        self.st["target"] = target
        self._save()
        # 1. Last wegnehmen
        self._set("draining", "Server wird aus dem Lastausgleich genommen", ident, version)
        self._drain(True)
        if not was_held:
            self.sleep(self.cfg.drain_seconds)
        # 2. Sicherung
        self._set("backing_up", "Sicherung vor dem Update", ident, version)
        try:
            backup = self.rt.backup(f"vor-update-{target}")
        except RuntimeFailure as exc:
            self._fail(ident, version, target, f"Sicherung fehlgeschlagen – Update nicht gestartet: {exc}", restored=False)
            return
        self.st["in_progress"]["backup"] = backup
        self._save()
        # 3. Neue Version starten
        self._set("updating", f"Starte Version {target}", ident, version)
        try:
            self.rt.apply_image(prep["ref"])
        except RuntimeFailure as exc:
            self._rollback(ident, version, target, f"Start fehlgeschlagen: {exc}")
            return
        # 4. Gesundheit
        self._set("verifying", "Gesundheitsprüfung", ident, version)
        ok, detail = self._wait_healthy(target)
        if policy.after_update(ok) == "keep":
            self._finish_ok(ident, target)
        else:
            self._rollback(ident, version, target, f"Gesundheitsprüfung fehlgeschlagen: {detail}")

    def _wait_healthy(self, expected_version: str) -> tuple[bool, str]:
        deadline = self.clock() + timedelta(seconds=self.cfg.health_timeout)
        good, detail = 0, "keine Antwort"
        while True:
            try:
                h: Health = self.rt.health()
            except RuntimeFailure as exc:
                h = Health(False, "", str(exc))
            if h.ok and (not expected_version or h.version == expected_version):
                good += 1
                if good >= self.cfg.health_ok_required:
                    return True, ""
            else:
                good = 0
                detail = h.detail or (f"Version {h.version!r} statt {expected_version!r}" if h.ok else "ungesund")
            if self.clock() >= deadline:
                return False, detail
            self.sleep(self.cfg.health_interval)

    def _finish_ok(self, ident: tuple[str, str], target: str) -> None:
        self._drain(False)
        self.st["highest"] = target
        self.st["in_progress"], self.st["prepared"], self.st["target"] = None, None, ""
        self.st["failed"].pop(target, None)
        self.offered = None
        self._log(f"Version {target} installiert und gesund")
        self._set("healthy", f"Version {target} läuft", ident, target)

    def _rollback(self, ident: tuple[str, str], version: str, target: str, reason: str) -> None:
        ip = self.st["in_progress"] or {}
        self._log(f"Rollback: {reason}")
        self._set("updating", f"Rollback: {reason}"[:280])
        restored = False
        try:
            if ip.get("prev_image"):
                self.rt.apply_image(ip["prev_image"])
            old_ok, _ = self._wait_healthy(ip.get("prev_version") or version)
        except RuntimeFailure:
            old_ok = False
        mig = ip.get("migration") or {"present": False, "backward_compatible": True}
        nxt = policy.after_image_rollback(old_healthy=old_ok, migration_present=mig["present"],
                                          backward_compatible=mig["backward_compatible"],
                                          allow_db_restore=bool(ip.get("allow_restore")),
                                          has_backup=bool(ip.get("backup")))
        if nxt == "restore_db":
            try:
                self.rt.restore(ip["backup"])
                restored = True
                self.rt.start_app()
                old_ok, _ = self._wait_healthy(ip.get("prev_version") or version)
            except RuntimeFailure as exc:
                old_ok = False
                reason += f" | Wiederherstellung fehlgeschlagen: {exc}"
        elif nxt == "give_up":
            old_ok = False
            reason += " | Rückkehr zur alten Version nicht möglich"
        self._fail(ident, version, target, reason, restored=restored, old_ok=old_ok)

    def _fail(self, ident: tuple[str, str], version: str, target: str, reason: str, *, restored: bool,
              old_ok: bool = True) -> None:
        if old_ok:
            self._drain(False)                               # alte Version läuft wieder: zurück in den Lastausgleich
        self.st["failed"][target] = reason[:300]
        self.st["in_progress"], self.st["prepared"] = None, None
        state = "rolled_back" if old_ok else "error"
        suffix = " (Sicherung eingespielt)" if restored else ""
        self._log(f"Update {target} gescheitert: {reason}{suffix}")
        self._set(state, f"{reason}{suffix}"[:280], ident, version)

    # ------------------------------------------------------------------ Wiederaufnahme nach Absturz
    def recover(self, ident: tuple[str, str], version: str) -> None:
        """Wurde der Agent mitten in einer Installation beendet, wird sie hier zu Ende geführt oder zurückgenommen."""
        ip = self.st.get("in_progress")
        if not ip:
            return
        self._log(f"Wiederaufnahme: Installation von {ip['version']} war unterbrochen")
        ok, detail = self._wait_healthy(ip["version"])
        if ok:
            self._finish_ok(ident, ip["version"])
        else:
            self._rollback(ident, version, ip["version"], f"unterbrochene Installation, {detail}")


# --------------------------------------------------------------------------- Betrieb
def config_from_env(env: dict[str, str] | None = None) -> Config:
    e = env if env is not None else os.environ
    pub = e.get("UPDATER_PUBKEY", "")
    pub_file = e.get("UPDATER_PUBKEY_FILE", "/etc/schulpuls/vendor.pub")
    if not pub and Path(pub_file).is_file():
        pub = Path(pub_file).read_text(encoding="utf-8").strip()
    if not pub:
        raise SystemExit("Kein Anbieter-Schlüssel hinterlegt (UPDATER_PUBKEY_FILE oder UPDATER_PUBKEY).")
    url = e.get("UPDATER_VENDOR_URL", "")
    if not url:
        raise SystemExit("UPDATER_VENDOR_URL fehlt.")
    node = e.get("UPDATER_NODE", "main")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,40}", node):
        raise SystemExit("UPDATER_NODE enthält ungültige Zeichen.")
    return Config(vendor_url=url, pubkey=pub, data_dir=Path(e.get("UPDATER_DATA_DIR", "/appdata")),
                  state_dir=Path(e.get("UPDATER_STATE_DIR", "/state")), node=node, node_id=e.get("SM_NODE_ID", node),
                  mode=e.get("UPDATER_MODE", "auto") if e.get("UPDATER_MODE", "auto") in ("auto", "manual") else "auto",
                  drain_seconds=float(e.get("UPDATER_DRAIN_SECONDS", "20")),
                  health_timeout=float(e.get("UPDATER_HEALTH_TIMEOUT", "300")),
                  min_free_mb=int(e.get("UPDATER_MIN_FREE_MB", "2048")),
                  allowed_registry=e.get("UPDATER_ALLOWED_REGISTRY", ""))
