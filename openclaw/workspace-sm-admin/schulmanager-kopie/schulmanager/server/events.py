"""Ereignisbus für Live-Updates (Server-Sent Events).

``bus.publish(event, data)`` ist thread-sicher und kann aus Sync-Handlern (Threadpool),
Worker-Threads oder dem Event-Loop aufgerufen werden. SSE-Clients (``GET /api/v1/events``)
erhalten die Ereignisse über je eine ``asyncio.Queue``; synchrone Listener
(``bus.add_listener(fn)``) werden direkt im publizierenden Thread aufgerufen – kurz halten!

Ereignisse laut Vertrag: ``change`` ``{version, scope, dates}``, ``job`` ``{id, status, progress, message}``,
``ping``. Optional kann ein Ereignis auf Benutzer mit einem Recht beschränkt werden
(``bus.publish("job", {...}, permission="timetable.generate")``).
"""
from __future__ import annotations

import asyncio
import itertools
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

log = logging.getLogger("schulmanager.events")

Listener = Callable[[str, dict], None]


@dataclass(eq=False)
class Subscription:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue
    permissions: frozenset[str] = frozenset()
    user_id: int | None = None
    lost: bool = False
    closed: bool = field(default=False)


class EventBus:
    def __init__(self, queue_size: int = 200) -> None:
        self._lock = threading.Lock()
        self._subs: set[Subscription] = set()
        self._listeners: list[Listener] = []
        self._ids = itertools.count(1)
        self.queue_size = queue_size
        self.published = 0

    # -------------------------------------------------------------- SSE-Clients
    def subscribe(self, permissions: set[str] | frozenset[str] = frozenset(),
                  user_id: int | None = None) -> Subscription:
        """Registriert einen SSE-Client (im laufenden Event-Loop aufrufen)."""
        sub = Subscription(asyncio.get_running_loop(), asyncio.Queue(self.queue_size), frozenset(permissions),
                           user_id)
        with self._lock:
            self._subs.add(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        sub.closed = True
        with self._lock:
            self._subs.discard(sub)

    @property
    def client_count(self) -> int:
        with self._lock:
            return len(self._subs)

    # -------------------------------------------------------------- Listener
    def add_listener(self, fn: Listener) -> None:
        """Synchroner Listener ``fn(event, data)`` (z. B. Benachrichtigungen)."""
        with self._lock:
            if fn not in self._listeners:
                self._listeners.append(fn)

    def remove_listener(self, fn: Listener) -> None:
        with self._lock:
            if fn in self._listeners:
                self._listeners.remove(fn)

    # -------------------------------------------------------------- Publizieren
    def publish(self, event: str, data: dict | None = None, *, permission: str | None = None,
                user_ids: set[int] | None = None) -> None:
        """Verteilt ein Ereignis an alle SSE-Clients und Listener (thread-sicher)."""
        data = dict(data or {})
        message = {"id": next(self._ids), "event": event, "data": data}
        self.published += 1
        with self._lock:
            subs = list(self._subs)
            listeners = list(self._listeners)
        for sub in subs:
            if permission and permission not in sub.permissions:
                continue
            if user_ids is not None and sub.user_id not in user_ids:
                continue
            try:
                sub.loop.call_soon_threadsafe(_put, sub, message)
            except RuntimeError:  # Loop bereits geschlossen
                self.unsubscribe(sub)
        for fn in listeners:
            try:
                fn(event, data)
            except Exception:  # noqa: BLE001 - Listener dürfen den Publisher nicht stören
                log.exception("Event-Listener %r fehlgeschlagen", fn)

    def clear(self) -> None:
        """Entfernt alle Clients und Listener (Shutdown/Tests)."""
        with self._lock:
            subs = list(self._subs)
            self._subs.clear()
            self._listeners.clear()
        for sub in subs:
            sub.closed = True
            try:
                sub.loop.call_soon_threadsafe(_put, sub, None)
            except RuntimeError:
                pass


def _put(sub: Subscription, message: dict | None) -> None:
    try:
        sub.queue.put_nowait(message)
    except asyncio.QueueFull:
        sub.lost = True


def format_sse(event: str, data: Any, event_id: int | None = None, retry: int | None = None) -> str:
    """Formatiert eine SSE-Nachricht."""
    lines = []
    if retry is not None:
        lines.append(f"retry: {retry}")
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    lines.extend(f"data: {line}" for line in payload.splitlines() or [""])
    return "\n".join(lines) + "\n\n"


async def sse_stream(sub: Subscription, is_disconnected: Callable[[], Any], hello: dict,
                     ping_seconds: float, poll_seconds: float = 5.0):
    """Async-Generator für die SSE-Antwort.

    Sendet sofort ``hello``, danach Ereignisse und spätestens alle ``ping_seconds`` ein ``ping``.
    Prüft alle ``poll_seconds`` auf Verbindungsabbruch und meldet das Abo im ``finally`` ab
    (auch wenn der Server den Generator bei Disconnect abbricht).
    """
    loop = asyncio.get_running_loop()
    try:
        yield format_sse("hello", hello, retry=3000)
        last_sent = loop.time()
        while not sub.closed:
            remaining = ping_seconds - (loop.time() - last_sent)
            try:
                message = await asyncio.wait_for(sub.queue.get(), timeout=max(0.05, min(poll_seconds, remaining)))
            except asyncio.TimeoutError:
                if await is_disconnected():
                    break
                if loop.time() - last_sent >= ping_seconds:
                    yield format_sse("ping", {})
                    last_sent = loop.time()
                continue
            if message is None:
                break
            if sub.lost:
                sub.lost = False
                # Ereignisse gingen verloren (Client zu langsam) → alles neu laden lassen
                yield format_sse("change", {"version": None, "scope": ["all"], "dates": [], "resync": True})
            yield format_sse(message["event"], message["data"], event_id=message["id"])
            last_sent = loop.time()
    finally:
        bus.unsubscribe(sub)


bus = EventBus()
