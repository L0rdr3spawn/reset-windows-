"""Server-Sent Events: ``GET /api/v1/events`` (Anmeldung nötig)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..config import config
from ..db import SessionLocal
from ..events import bus, sse_stream
from ..runtime import ensure_started

router = APIRouter(tags=["Live-Updates"])


@router.get("/events")
async def events(request: Request) -> StreamingResponse:
    """Ereignisstrom: ``hello`` (sofort), ``change`` ``{version,scope,dates}``, ``job``, ``ping`` (alle 20 s)."""
    from ..deps import authenticate
    from ..store import get_store

    def auth():
        ensure_started()
        with SessionLocal() as db:  # kurzlebige Session – nicht für die gesamte Stream-Dauer halten
            return authenticate(request, db), get_store().version

    user, version = await asyncio.to_thread(auth)
    if user is None:
        raise HTTPException(401, "not_authenticated")
    sub = bus.subscribe(user.permissions, user.id)
    hello = {"version": version, "user": user.username}
    return StreamingResponse(
        sse_stream(sub, request.is_disconnected, hello, config.sse_ping_seconds),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
