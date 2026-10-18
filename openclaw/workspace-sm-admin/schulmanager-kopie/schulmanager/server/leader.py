"""Leader-Sperre für den Betrieb mit mehreren Knoten (``SM_HA=1``).

Mehrere App-Knoten teilen sich **eine** PostgreSQL-Datenbank und eine Dateiablage. Hintergrundjobs (Benachrichtigungen,
Autoplaner, Mail-Abruf, Ferienimport, Wartung) dürfen aber nur auf **einem** Knoten laufen – sonst entstehen doppelte
Mails und doppelte Wartungsläufe. Der Knoten, der die Sperre (eine Zeile in ``system_state``) hält, ist der *Leader*.

Verfahren: Pacht (Lease) mit Ablaufzeit. Der Leader verlängert sie regelmäßig; fällt er aus, übernimmt ein anderer Knoten
nach Ablauf (``ttl`` Sekunden). Die Übernahme ist eine bedingte Aktualisierung (compare-and-swap über ``updated_at``) –
zwei Knoten können die Pacht nie gleichzeitig bekommen. Voraussetzung: die Uhren der Knoten gehen ähnlich (NTP).

Ohne ``SM_HA`` ist der einzige Knoten immer Leader (:func:`is_leader` gibt ``True``).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from .config import config
from .db import session_scope, utcnow
from .feature_models.ops import SystemState

log = logging.getLogger("schulmanager.leader")

LEASE_KEY = "leader:jobs"


class Lease:
    """Pacht auf eine benannte Rolle in der Datenbank (testbar mit eigener Uhr)."""

    def __init__(self, node_id: str, *, key: str = LEASE_KEY, ttl: float = 30.0,
                 clock: Callable[[], float] = time.time) -> None:
        self.node_id, self.key, self.ttl, self.clock = node_id, key, ttl, clock
        self.held = False

    def holder(self) -> Optional[dict]:
        """Aktueller Inhaber ``{"node", "until"}`` oder ``None`` (keiner / abgelaufen)."""
        with session_scope() as db:
            row = db.get(SystemState, self.key)
            val = row.value if row is not None else None
        if isinstance(val, dict) and float(val.get("until", 0)) > self.clock():
            return val
        return None

    def acquire(self) -> bool:
        """Pacht übernehmen oder verlängern. ``True``, wenn dieser Knoten sie danach hält."""
        now = self.clock()
        new = {"node": self.node_id, "until": now + self.ttl}
        try:
            with session_scope() as db:
                row = db.get(SystemState, self.key)
                if row is None:
                    db.add(SystemState(key=self.key, value=new, updated_at=utcnow(), updated_by=self.node_id))
                    db.flush()
                    self.held = True
                    return True
                val = row.value if isinstance(row.value, dict) else {}
                mine = val.get("node") == self.node_id
                expired = float(val.get("until", 0)) <= now
                if not (mine or expired):
                    self.held = False
                    return False
                res = db.execute(update(SystemState).where(SystemState.key == self.key,
                                                           SystemState.updated_at == row.updated_at)
                                 .values(value=new, updated_at=utcnow(), updated_by=self.node_id))
                self.held = res.rowcount == 1
                return self.held
        except IntegrityError:                    # ein anderer Knoten war in derselben Millisekunde schneller
            self.held = False
            return False

    def release(self) -> None:
        """Pacht freigeben (sauberes Beenden), damit ein anderer Knoten sofort übernehmen kann."""
        if not self.held:
            return
        self.held = False
        with session_scope() as db:
            row = db.get(SystemState, self.key)
            if row is not None and isinstance(row.value, dict) and row.value.get("node") == self.node_id:
                db.execute(update(SystemState).where(SystemState.key == self.key, SystemState.updated_at == row.updated_at)
                           .values(value={"node": self.node_id, "until": 0}, updated_at=utcnow()))


_lease: Optional[Lease] = None
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_callbacks: tuple[Optional[Callable[[], None]], Optional[Callable[[], None]]] = (None, None)


def is_leader() -> bool:
    """Darf dieser Knoten Hintergrundjobs ausführen?"""
    if not config.ha:
        return True
    return bool(_lease and _lease.held)


def _loop(interval: float) -> None:
    assert _lease is not None
    was = False
    while not _stop.is_set():
        try:
            now_leader = _lease.acquire()
        except Exception:  # noqa: BLE001 – Datenbank kurz weg: Pacht läuft aus, Jobs stoppen
            log.exception("Leader-Pacht konnte nicht erneuert werden")
            _lease.held = False
            now_leader = False
        gain, lose = _callbacks
        try:
            if now_leader and not was:
                log.info("Knoten %s ist jetzt Leader (Hintergrundjobs starten)", _lease.node_id)
                if gain:
                    gain()
            elif was and not now_leader:
                log.warning("Knoten %s ist nicht mehr Leader (Hintergrundjobs stoppen)", _lease.node_id)
                if lose:
                    lose()
        except Exception:  # noqa: BLE001
            log.exception("Leader-Wechsel fehlgeschlagen")
        was = now_leader
        _stop.wait(interval)


def start(on_gain: Callable[[], None] | None = None, on_lose: Callable[[], None] | None = None, *,
          ttl: float = 30.0, interval: float = 10.0) -> None:
    """Pacht-Wächter starten (nur bei ``SM_HA=1``; sonst nichts)."""
    global _lease, _thread, _callbacks
    if not config.ha or (_thread is not None and _thread.is_alive()):
        return
    _lease = Lease(config.node_id, ttl=ttl)
    _callbacks = (on_gain, on_lose)
    _stop.clear()
    _thread = threading.Thread(target=_loop, args=(interval,), name="sm-leader", daemon=True)
    _thread.start()


def stop() -> None:
    global _thread
    _stop.set()
    if _thread is not None:
        _thread.join(timeout=5)
        _thread = None
    gain, lose = _callbacks
    if _lease is not None and _lease.held:
        try:
            if lose:
                lose()
        finally:
            _lease.release()
