"""Schnittstelle zwischen App und Update-Agent (Begleitdienst, ``updater/``) über Dateien im Datenordner.

* ``updater/status.json`` – schreibt der Agent (Stand, angebotene Version, Zeitfenster, Protokoll), die App liest nur.
* ``updater/plan.json`` – schreibt die App (Wünsche der Administration: verschieben, „nur manuell“, „Jetzt installieren“),
  der Agent liest nur und prüft selbst die Grenzen (höchstens 7 Tage, nur einmal je Version, nie bei dringenden Updates).

Die App führt nie selbst ein Update aus und hat keinen Zugriff auf den Docker-Socket.
"""
from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .config import APP_VERSION, config

log = logging.getLogger("schulmanager.updates")

MAX_POSTPONE_DAYS = 7


def updater_dir() -> Path:
    return config.data_dir / "updater"


def read_status() -> dict | None:
    """Stand des Agenten oder ``None`` (kein Agent eingerichtet bzw. noch nie gelaufen)."""
    try:
        data = json.loads((updater_dir() / "status.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def read_plan() -> dict:
    try:
        data = json.loads((updater_dir() / "plan.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_plan(plan: dict) -> None:
    d = updater_dir()
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "plan.json.tmp"
    tmp.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(d / "plan.json")


def postpone(version: str, days: int, *, now: datetime | None = None) -> dict:
    """Einmalige Verschiebung des angebotenen Updates (schreibt den Wunsch; der Agent setzt ihn um)."""
    st = read_status() or {}
    offered = st.get("offered") or {}
    if offered.get("version") != version:
        raise ValueError("Für diese Version liegt kein Update vor.")
    if st.get("urgent"):
        raise ValueError("Dringende Sicherheitsupdates können nicht verschoben werden.")
    if not st.get("can_postpone"):
        raise ValueError("Dieses Update wurde bereits einmal verschoben.")
    if not 1 <= days <= MAX_POSTPONE_DAYS:
        raise ValueError(f"Sie können um 1 bis {MAX_POSTPONE_DAYS} Tage verschieben.")
    until = (now or datetime.now(timezone.utc)) + timedelta(days=days)
    plan = read_plan()
    plan["postpone"] = {"version": version, "until": until.strftime("%Y-%m-%dT%H:%M:%SZ")}
    write_plan(plan)
    return plan["postpone"]


def install_now(version: str) -> dict:
    st = read_status() or {}
    if (st.get("offered") or {}).get("version") != version:
        raise ValueError("Für diese Version liegt kein Update vor.")
    plan = read_plan()
    plan["install_now"] = {"id": secrets.token_hex(8), "version": version}
    write_plan(plan)
    return plan["install_now"]


def set_mode(mode: str) -> None:
    if mode not in ("auto", "manual"):
        raise ValueError("Unbekannter Modus.")
    plan = read_plan()
    plan["mode"] = mode
    write_plan(plan)


def set_strategy(strategy: str) -> None:
    if strategy not in ("simultaneous", "rolling"):
        raise ValueError("Unbekannte Strategie.")
    plan = read_plan()
    plan["strategy"] = strategy
    write_plan(plan)


def overview() -> dict[str, Any]:
    st = read_status()
    plan = read_plan()
    stale = True
    if st and st.get("updated_at"):
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(str(st["updated_at"]).replace("Z", "+00:00"))
            stale = age > timedelta(hours=1)
        except ValueError:
            pass
    return {"version": APP_VERSION, "node": config.node_id, "agent": st is not None, "agent_stale": stale if st else None,
            "status": st, "plan": plan, "max_postpone_days": MAX_POSTPONE_DAYS}


def record_startup() -> None:
    """Merkt die laufende Version; ändert sie sich (Update oder Rollback), kommt ein Eintrag ins Audit-Protokoll."""
    from . import ops
    from .audit import audit_now

    key = f"app_version:{config.node_id}"
    try:
        last = ops.get_state(key)
        if last != APP_VERSION:
            ops.set_state(key, APP_VERSION, by="system")
            if last:
                audit_now(None, "update.version_changed", config.node_id, {"from": last, "to": APP_VERSION})
    except Exception:  # noqa: BLE001 – darf den Start nie verhindern
        log.exception("Versionswechsel konnte nicht protokolliert werden")
