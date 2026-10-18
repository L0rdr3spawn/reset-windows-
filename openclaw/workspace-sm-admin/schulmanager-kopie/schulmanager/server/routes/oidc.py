"""Single Sign-on über das Schulkonto (OpenID Connect) – alte Pfade ``/auth/oidc/*``.

Seit §11.4 (Anmeldedienste) ist das Schulkonto der Anbieter ``oidc`` der gemeinsamen Umsetzung in
``routes/features_sso.py`` und ``server/sso_providers.py`` (Authorization Code Flow + PKCE + nonce). Diese Pfade
bleiben, weil die Redirect-URI beim Identity Provider eingetragen ist.

Konfiguration: ``SM_OIDC_ISSUER``, ``SM_OIDC_CLIENT_ID``, ``SM_OIDC_CLIENT_SECRET`` (optional bei Public Clients),
``SM_OIDC_SCOPES`` (``openid profile email``), ``SM_OIDC_USERNAME_CLAIM`` (``preferred_username``),
``SM_OIDC_AUTO_CREATE`` (0), ``SM_OIDC_DEFAULT_ROLE`` (``lehrer``), ``SM_OIDC_LABEL`` – oder im Admin-Bereich
„Anmeldedienste“ (Umgebungsvariablen haben Vorrang).
Redirect-URI beim Identity Provider eintragen (unverändert): ``{SM_BASE_URL}/api/v1/auth/oidc/callback``.

Ablauf: ``GET /auth/oidc/login?next=/pfad`` (wie ``/auth/sso/oidc/login``) → IdP → ``GET /auth/oidc/callback`` →
Sitzungs-Cookie, Weiterleitung auf ``next``. Fehler: ``/login?sso_error=<code>`` (``not_configured``, ``state``,
``provider``, ``unknown_user``, ``account_disabled``, ``method_not_allowed`` …).
Das ID-Token kommt direkt per TLS vom Token-Endpunkt; laut OIDC Core 3.1.3.7 ersetzt die TLS-Prüfung dort die
Signaturprüfung. Geprüft werden ``iss``, ``aud``, ``exp`` und ``nonce``. Verknüpfungen liegen in ``user_identities``
(früher ``users.oidc_sub``, von Migration 0010 übernommen); erstmalig über Benutzername bzw. E-Mail; 2FA übernimmt der
Identity Provider. In Tests ersetzbar: ``_http_json``; ``_discovery`` ist der gemeinsame Discovery-Cache.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import sso_providers as sso
from ..db import get_db

router = APIRouter(prefix="/auth/oidc", tags=["Anmeldung"])

_discovery = sso._discovery   # gemeinsamer Cache (Tests: ``oidc._discovery.clear()``)


def _http_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    """Abruf beim Identity Provider (delegiert an ``sso_providers._http_json``). In Tests ersetzbar."""
    return sso._http_json(url, data, headers)


_http_json._sm_delegate = True  # type: ignore[attr-defined]  # ersetzt → sso_providers.http_json nutzt den Ersatz


def discovery() -> dict:
    """Metadaten des per Umgebung eingerichteten Schulkontos (kompatibel zur alten Schnittstelle)."""
    return sso.discovery(sso.resolve(None, "oidc").issuer or "")


def decode_id_token(token: str) -> dict:
    return sso.decode_id_token(token)


def _safe_next(value: str | None) -> str:
    from .features_sso import safe_next

    return safe_next(value)


@router.get("/login")
def oidc_login(next: str | None = None,  # noqa: A002 - Query-Parameter heißt so
               db: Session = Depends(get_db)) -> RedirectResponse:
    from .features_sso import start_login

    return start_login(db, "oidc", next, legacy=True)


@router.get("/callback")
def oidc_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None,
                  db: Session = Depends(get_db)) -> RedirectResponse:
    from .features_sso import finish, login_error

    if not sso.resolve(db, "oidc").enabled:
        return login_error("not_configured", "oidc")
    return finish(request, db, "oidc", code, state, error)
