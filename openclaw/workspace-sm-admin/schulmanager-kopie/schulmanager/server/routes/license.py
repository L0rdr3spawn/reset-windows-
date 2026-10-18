"""Lizenz der Schule (``licensing``): Stand anzeigen, Lizenzschlüssel eintragen, jetzt beim Lizenzserver prüfen.

* ``GET /license`` – alle Angemeldeten: Kurzstand (für den Hinweis-Balken); mit ``license.manage`` (Administration,
  Schulleitung): alles.
* ``PUT /license`` – ``license.manage``: Lizenzschlüssel eintragen (``{"key": "SPUL-…"}``); Prüfziffer, dann Aktivierung (Bindung) beim Lizenzserver.
* ``POST /license/check`` – ``license.manage``: sofort beim Lizenzserver bestätigen lassen.

Diese Routen bleiben auch bei gesperrter Lizenz offen (``app.LicenseLockMiddleware``), damit die Lizenz wieder
eingespielt werden kann; wer nicht ``license.manage`` hat, kommt dann nicht über den Kurzstand hinaus.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..audit import audit
from ..db import get_db
from ..deps import AuthUser, client_ip, current_user, require

router = APIRouter(tags=["Lizenz"])
SHORT_KEYS = ("state", "stage", "read_only", "locked", "reason", "message", "warning", "enforced", "days_left",
              "grace_until")


class LicenseIn(BaseModel):
    key: str = Field(min_length=10, max_length=64)


@router.get("/license")
def get_license(user: AuthUser = Depends(current_user)) -> dict:
    from .. import licensing
    full = "license.manage" in user.permissions
    st = licensing.status(full=full)
    if full:
        return st
    return {k: st.get(k) for k in SHORT_KEYS}


@router.put("/license")
def put_license(body: LicenseIn, request: Request, user: AuthUser = Depends(require("license.manage")),
                db: Session = Depends(get_db)) -> dict:
    from .. import licensing
    try:
        st = licensing.install(body.key)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    audit(db, user, "license.install", "license", {"key_last4": st.get("key_last4"), "licensee": st.get("licensee")},
          ip=client_ip(request))
    db.commit()
    return st


@router.post("/license/check")
def check_license(user: AuthUser = Depends(require("license.manage"))) -> dict:
    from .. import licensing
    licensing.check_now()
    return licensing.status(full=True)
