"""Start des Update-Agenten: ``python -m updater`` (Dauerbetrieb) oder ``python -m updater --once``."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

from .agent import Agent, config_from_env
from .client import UrllibTransport, VendorClient
from .runtime import DockerRuntime


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m updater")
    ap.add_argument("--once", action="store_true", help="einen Durchlauf ausführen und beenden")
    args = ap.parse_args(argv)
    logging.basicConfig(level=os.environ.get("UPDATER_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    cfg = config_from_env()
    insecure = os.environ.get("UPDATER_ALLOW_INSECURE") == "1" and os.environ.get("SM_MODE") != "production"
    client = VendorClient(cfg.vendor_url, UrllibTransport(allow_insecure=insecure))
    runtime = DockerRuntime(Path(os.environ.get("UPDATER_COMPOSE_DIR", "/deploy")),
                            health_url=os.environ.get("UPDATER_HEALTH_URL", "http://app:8000/healthz"),
                            project=os.environ.get("COMPOSE_PROJECT_NAME", ""))
    agent = Agent(cfg, client, runtime)
    stop = {"now": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(now=True))
    signal.signal(signal.SIGINT, lambda *_: stop.update(now=True))
    poll_s = max(30, int(os.environ.get("UPDATER_POLL_SECONDS", "900")))
    while not stop["now"]:
        try:
            step = agent.tick()
            logging.info("Durchlauf: %s (%s) %s", step.action, step.state, step.detail)
        except Exception:  # noqa: BLE001 – der Agent darf nie abstürzen
            logging.exception("Durchlauf fehlgeschlagen")
        if args.once:
            break
        # im Zeitfenster bzw. bei Auftrag häufiger fragen
        fast = agent.st["state"] in ("ready", "postponed", "waiting", "downloading") and agent.offered is not None
        for _ in range(60 if fast else poll_s):
            if stop["now"]:
                break
            time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
