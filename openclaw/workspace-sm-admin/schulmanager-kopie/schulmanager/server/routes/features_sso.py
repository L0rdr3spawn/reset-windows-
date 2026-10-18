"""Anmeldedienste: mit Microsoft, Apple, Google oder dem Schulkonto anmelden und Konten verbinden (§11.4).

Öffentlich (ohne Anmeldung)
---------------------------
* ``GET  /auth/sso/providers`` → ``[{id, label, mock, flow, auto, client_id?, redirect_uri?}]`` (Login-Seite;
  ``flow``: ``redirect``, ``microsoft``, ``gis`` = Google Identity Services, ``apple_js`` = Sign in with Apple JS).
* ``GET  /auth/sso/{provider}/login?next=&add=&silent=&hint=`` → Weiterleitung zum Anbieter (bzw. zur Seite des
  Test-Anbieters). ``add=true``: weiteres Konto anmelden (bisherige bleiben angemeldet). ``silent=true`` (+ ``hint`` =
  E-Mail): stilles SSO (``prompt=none``); ohne Anbieter-Sitzung → ``/login?sso_silent=failed`` ohne Fehlermeldung.
* ``POST /auth/sso/{provider}/nonce`` (``google``/``apple``) → ``{nonce}`` + Status-Cookie; ``POST
  /auth/sso/{provider}/token`` ``{id_token, next?, add?}`` → Anmeldung mit einem ID-Token, das der Browser direkt
  bekommen hat (One Tap / Apple-Popup): Signatur (JWKS), ``iss``, ``aud``, ``exp``, ``nonce`` werden geprüft; danach
  derselbe Weg wie beim Callback (Verknüpfung, Login-Richtlinie, ``active``). Antwort wie ``/auth/login`` + ``next``.
* ``GET|POST /auth/sso/{provider}/callback`` – Rückkehr vom Anbieter (Apple: ``form_post`` → POST).
  Anmelden: Verknüpfung → Konto (sonst vorgemerkte Adresse bzw. ``sso_create``, siehe ``identities.find_login_user``),
  dann ``login_policy.method_allowed`` und ``active``. Fehler → ``/login?sso_error=<code>``: ``state``, ``provider``,
  ``cancelled``, ``provider_disabled``, ``unknown_user``, ``account_disabled``, ``method_not_allowed``,
  ``email_unverified``, ``domain_not_allowed``.
* ``GET|POST /auth/sso/{provider}/mock`` – Test-Anbieter (nur Entwicklung, ``SM_SSO_DEV_MOCK``, nicht eingerichteter
  Anbieter): schlichte Seite ohne JavaScript (E-Mail + Name) → Callback mit signiertem Test-Code.

Angemeldet
----------
* ``GET    /me/identities`` – verbunden, verfügbar, Pflicht laut Richtlinie, ``self_link``, je Anbieter ``can_link``/
  ``can_unlink`` (+ Begründung).
* ``POST   /me/identities/{provider}/link`` ``{next?}`` → ``{url}``; der signierte Status enthält Konto + Sitzung, der
  Callback verbindet nur, solange genau diese Sitzung angemeldet ist. Danach ``next`` (Standard ``/profil``) mit
  ``?verbunden=<provider>`` bzw. ``?sso_error=<code>`` (``already_linked``, ``already_connected``,
  ``link_not_allowed``; abgelaufene Sitzung → ``/login?sso_error=link_expired``).
* ``DELETE /me/identities/{provider}`` – nur mit ``self_link``, nicht bei Pflicht-Anbietern und nur, wenn ein anderer
  erlaubter Anmeldeweg bleibt (Passwort gesetzt + erlaubt oder anderer verbundener, verfügbarer, erlaubter Anbieter).
* Verwaltung (``users.manage`` + Rollenbereich): ``GET /users/{id}/identities``, ``POST /users/{id}/identities``
  ``{provider, email}`` (vormerken), ``DELETE /users/{id}/identities/{provider}``.
* Einrichtung (nur Rolle ``admin``): ``GET /sso/providers/config`` (Geheimnisse nie, nur „gesetzt“),
  ``PUT /sso/providers/{provider}`` (Geheimnisse verschlüsselt, leeres Feld = unverändert),
  ``POST /sso/providers/{provider}/test`` (Discovery abrufen, Apple: Schlüssel prüfen).
"""
from __future__ import annotations

import hmac
import html
import logging
import re
import urllib.parse
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...branding import PRODUCT_NAME
from .. import sso_providers as sso
from ..audit import audit
from ..config import config
from ..db import get_db, iso, utcnow
from ..db_models import User, UserSession
from ..deps import SESSION_COOKIE, AuthUser, client_ip, current_user, require
from ..feature_models.identities import SsoProvider, UserIdentity
from .. import net_guard
from ..identities import PROVIDERS, available_providers, identity_rows, public_identity
from ..security import hash_token

log = logging.getLogger("schulmanager.sso")

router = APIRouter(tags=["Anmeldedienste"])

COOKIE_PATH = "/api/v1/auth"
CANCEL_ERRORS = frozenset({"access_denied", "user_cancelled_authorize", "consent_required", "interaction_required"})
#: Antworten des Anbieters auf ``prompt=none``, wenn keine (passende) Anbieter-Sitzung besteht
SILENT_ERRORS = frozenset({"login_required", "interaction_required", "consent_required", "account_selection_required"})
HINT_COOKIE = "sm_sso_hint"          # Kennung des zuletzt benutzten Anbieters (lesbar für die Anmeldeseite)
HINT_WHO_COOKIE = "sm_sso_who"       # E-Mail für stilles SSO, **verschlüsselt** und httponly; beim Abmelden gelöscht
TOKEN_PROVIDERS = frozenset({"google", "apple"})


# =========================================================================== Hilfen
def state_cookie(provider: str) -> str:
    return f"sm_sso_{provider}"


def safe_next(value: str | None, default: str = "/") -> str:
    """Nur interne Pfade (kein Open Redirect, keine Steuer-/Leerzeichen, keine API-Pfade)."""
    if not value or len(value) > 500:
        return default
    if not value.startswith("/") or value.startswith("//") or "\\" in value:
        return default
    if any(ord(c) < 33 or ord(c) == 127 for c in value) or value.startswith(("/api/", "/login")):
        return default
    return value


def with_query(path: str, **params: str) -> str:
    path, _, fragment = path.partition("#")       # Anker zuerst abtrennen (steht hinter der Abfrage)
    base, _, query = path.partition("?")
    items = [(k, v) for k, v in urllib.parse.parse_qsl(query, keep_blank_values=True) if k not in params]
    items += list(params.items())
    return f"{base}?{urllib.parse.urlencode(items)}" + (f"#{fragment}" if fragment else "")


def _known(provider: str) -> str:
    if provider not in PROVIDERS:
        raise HTTPException(404, "Unbekannter Anmeldedienst")
    return provider


def _label(db: Session, provider: str) -> str:
    return sso.resolve(db, provider).label


def set_state_cookie(resp, provider: str, value: str) -> None:
    """Status-Cookie (httponly, 10 min). Apple sendet per POST von appleid.apple.com zurück → bei https SameSite=None."""
    if provider in sso.FORM_POST and config.base_url.startswith("https://"):
        resp.set_cookie(state_cookie(provider), value, max_age=sso.STATE_TTL, httponly=True, samesite="none",
                        secure=True, path=COOKIE_PATH)
    else:
        resp.set_cookie(state_cookie(provider), value, max_age=sso.STATE_TTL, httponly=True, samesite="lax",
                        secure=config.cookie_secure, path=COOKIE_PATH)


def _done(resp, provider: str | None):
    if provider:
        resp.delete_cookie(state_cookie(provider), path=COOKIE_PATH)
    return resp


def _who_aad(provider: str) -> str:
    return f"sso_hint:{provider}"


def set_hint_cookie(resp, provider: str, email: str | None) -> None:
    """Merkt den Anbieter für stilles SSO/Auto-Auswahl (nur die Kennung, lesbar für die Anmeldeseite, 90 Tage). Die
    E-Mail-Adresse steht nie im Klartext im Browser: verschlüsselt in einem httponly-Cookie, das nur der Server liest."""
    if email:
        from .. import crypto

        resp.set_cookie(HINT_COOKIE, provider, max_age=90 * 86400, httponly=False, samesite="lax",
                        secure=config.cookie_secure, path="/")
        resp.set_cookie(HINT_WHO_COOKIE, crypto.encrypt_text(email, _who_aad(provider)), max_age=90 * 86400,
                        httponly=True, samesite="lax", secure=config.cookie_secure, path="/")


def hinted_email(request: Request | None, provider: str) -> str | None:
    """E-Mail aus dem verschlüsselten Hinweis-Cookie (für ``login_hint``); ``None`` bei Fehlern/anderem Anbieter."""
    raw = request.cookies.get(HINT_WHO_COOKIE) if request is not None else None
    if not raw or request.cookies.get(HINT_COOKIE) != provider:
        return None
    try:
        from .. import crypto

        value = crypto.decrypt_text(raw, _who_aad(provider))
    except Exception:  # noqa: BLE001 - manipuliert/fremder Schlüssel
        return None
    return value if "@" in value and len(value) <= 254 else None


def login_error(code: str, provider: str | None = None) -> RedirectResponse:
    return _done(RedirectResponse(f"/login?sso_error={code}", status_code=303), provider)


def _link_error(saved: dict, code: str, provider: str) -> RedirectResponse:
    if code == "link_expired":
        return login_error(code, provider)
    target = safe_next(saved.get("nx"), "/profil")
    return _done(RedirectResponse(with_query(target, sso_error=code), status_code=303), provider)


def _policy(db: Session, user):
    from .. import login_policy

    return login_policy.effective_policy(db, user)


# =========================================================================== Öffentlich: Anmeldung
@router.get("/auth/sso/providers")
def sso_provider_list(db: Session = Depends(get_db)) -> list[dict]:
    """Nutzbare Anmeldedienste für die Login-Seite (``mock`` = Test-Anbieter)."""
    return available_providers(db)


def start_login(db: Session, provider: str, next_path: str | None, *, legacy: bool = False,
                request: Request | None = None, add: bool = False, silent: bool = False,
                hint: str | None = None) -> RedirectResponse:
    if provider not in PROVIDERS:
        return login_error("provider_disabled")
    cfg = sso.resolve(db, provider)
    if legacy and not cfg.enabled:
        return login_error("not_configured", provider)
    if not cfg.usable:
        return login_error("provider_disabled", provider)
    try:
        if hint is None and silent and not legacy:
            hint = hinted_email(request, provider)
        keep = None
        if add and request is not None:
            from .auth import current_sessions

            keep = current_sessions(request)
        url, cookie = sso.new_flow(cfg, mode="login", next_path=safe_next(next_path), silent=silent and not legacy,
                                   login_hint=hint, keep_sessions=keep)
    except Exception:  # noqa: BLE001
        log.exception("Anmeldedienst %s: Start fehlgeschlagen", provider)
        return login_error("provider", provider)
    resp = RedirectResponse(url, status_code=302)
    set_state_cookie(resp, provider, cookie)
    return resp


@router.get("/auth/sso/{provider}/login")
def sso_login(provider: str, request: Request, next: str | None = None,  # noqa: A002 - Query-Parameter heißt so
              add: bool = False, silent: bool = False, hint: str | None = Query(None, max_length=254),
              db: Session = Depends(get_db)) -> RedirectResponse:
    return start_login(db, provider, next, request=request, add=add, silent=silent, hint=hint)


@router.get("/auth/sso/{provider}/callback")
def sso_callback_get(provider: str, request: Request, code: str | None = None, state: str | None = None,
                     error: str | None = None, db: Session = Depends(get_db)) -> RedirectResponse:
    return finish(request, db, provider, code, state, error)


@router.post("/auth/sso/{provider}/callback")
def sso_callback_post(provider: str, request: Request, code: str | None = Form(None, max_length=4096),
                      state: str | None = Form(None, max_length=512), error: str | None = Form(None, max_length=200),
                      db: Session = Depends(get_db)) -> RedirectResponse:
    """Apple (``response_mode=form_post``). Kein CSRF-Header nötig: geschützt durch Status-Cookie + ``state``."""
    return finish(request, db, provider, code, state, error)


def finish(request: Request, db: Session, provider: str, code: str | None, state: str | None,
           error: str | None) -> RedirectResponse:
    """Gemeinsamer Callback (auch für die alten Pfade ``/auth/oidc/*``)."""
    if provider not in PROVIDERS:
        return login_error("provider_disabled")
    saved = sso.unsign(request.cookies.get(state_cookie(provider)), "state")
    if saved is None or saved.get("p") != provider or not state \
            or not hmac.compare_digest(str(state), str(saved.get("s", ""))):
        return login_error("state", provider)
    link = saved.get("m") == "link"
    if saved.get("si") and error and not link:
        return _silent_failed(saved, provider, error)

    def fail(code_: str) -> RedirectResponse:
        return _link_error(saved, code_, provider) if link else login_error(code_, provider)

    if error:
        return fail("cancelled" if error in CANCEL_ERRORS else "provider")
    if not code:
        return fail("state")
    cfg = sso.resolve(db, provider)
    if not cfg.usable or bool(saved.get("mock")) != cfg.mock:
        return fail("provider_disabled")
    if link:
        session = _link_session(request, db, saved)
        if session is None:
            return fail("link_expired")
    try:
        meta = sso.metadata(cfg)
        claims = sso.fetch_claims(cfg, meta, code, saved)
        ident = sso.identity_from_claims(cfg, claims)
    except sso.ProviderError as exc:
        log.warning("Anmeldedienst %s: %s", provider, exc)
        return fail("provider")
    except Exception:  # noqa: BLE001
        log.exception("Anmeldedienst %s: Anmeldung fehlgeschlagen", provider)
        return fail("provider")
    problem = sso.domain_problem(cfg, ident)
    if problem:
        return fail(problem)
    if link:
        return _finish_link(request, db, cfg, ident, saved, session)
    return _finish_login(request, db, cfg, ident, saved)


def _silent_failed(saved: dict, provider: str, error: str) -> RedirectResponse:
    """Stilles SSO ging nicht (kein Anbieter-Konto angemeldet): zurück zur Anmeldeseite – ohne Fehlermeldung."""
    nx = safe_next(saved.get("nx"))
    code = "failed" if error in SILENT_ERRORS else "error"
    target = with_query("/login", sso_silent=code, **({"next": nx} if nx != "/" else {}))
    return _done(RedirectResponse(target, status_code=303), provider)


def _authenticate(request: Request, db: Session, cfg: sso.ProviderConfig, ident: sso.Identity):
    """Anbieter-Konto → Schulmanager-Konto. Ergebnis: ``(user, how)`` oder ein Fehlercode (``str``).

    Regeln unverändert (``identities.find_login_user``: Verknüpfung, vorgemerkte bzw. bestätigte Adresse, Anlegen nur,
    wenn die Schule es erlaubt), danach Login-Richtlinie und ``active``."""
    from .. import identities, login_policy

    ip = client_ip(request)
    user, row, how = identities.find_login_user(db, cfg, ident)
    if user is None or row is None:
        db.rollback()
        log.info("Anmeldedienst %s: kein passendes Konto", cfg.id)
        return "unknown_user"
    if not login_policy.method_allowed(db, user, cfg.id):
        db.rollback()
        audit(db, user, "auth.login_denied", f"user:{user.id}", {"method": cfg.id, "reason": "method_not_allowed"},
              ip=ip)
        db.commit()
        return "method_not_allowed"
    if not user.active:
        db.rollback()
        return "account_disabled"
    row.last_login_at = utcnow()
    if ident.email:
        row.email, row.email_verified = ident.email, bool(ident.email_verified)
    if how != "linked":
        audit(db, user, "identity.link", f"user:{user.id}",
              {"provider": cfg.id, "via": how, "email": ident.email, "mock": cfg.mock}, ip=ip)
    return user, how


def _finish_login(request: Request, db: Session, cfg: sso.ProviderConfig, ident: sso.Identity,
                  saved: dict) -> RedirectResponse:
    from .auth import keep_sessions, login_user

    res = _authenticate(request, db, cfg, ident)
    if isinstance(res, str):
        return login_error(res, cfg.id)
    user = res[0]
    resp = RedirectResponse(safe_next(saved.get("nx")), status_code=303)
    login_user(db, user, request, resp, method=cfg.id)
    if saved.get("ks"):
        keep_sessions(db, resp, [str(t) for t in saved["ks"]], user.id, request)
    set_hint_cookie(resp, cfg.id, ident.email)
    return _done(resp, cfg.id)


# =========================================================================== ID-Token aus dem Browser (One Tap, Apple JS)
class TokenBody(BaseModel):
    id_token: str = Field(max_length=sso.ID_TOKEN_MAX)
    next: str | None = Field(default=None, max_length=500)
    add: bool = False


def _token_provider(db: Session, provider: str) -> sso.ProviderConfig:
    if provider not in TOKEN_PROVIDERS:
        raise HTTPException(404, "Nicht gefunden")
    cfg = sso.resolve(db, provider)
    if not cfg.enabled or cfg.mock:
        raise HTTPException(409, {"code": "provider_disabled", "message": SSO_TOKEN_MESSAGES["provider_disabled"]})
    return cfg


SSO_TOKEN_MESSAGES = {
    "provider_disabled": "Dieser Anmeldedienst ist nicht (mehr) eingerichtet.",
    "state": "Die Anmeldung ist abgelaufen – bitte erneut versuchen.",
    "provider": "Der Anmeldedienst hat einen Fehler gemeldet. Bitte später erneut versuchen.",
}


@router.post("/auth/sso/{provider}/nonce")
def sso_nonce(provider: str, db: Session = Depends(get_db)) -> JSONResponse:
    """Nonce für das Anmelden mit einem vom Browser gelieferten ID-Token. Der Nonce hängt am Status-Cookie dieses
    Browsers – ein fremdes oder mitgeschnittenes Token passt dort nicht."""
    cfg = _token_provider(db, provider)
    nonce, cookie = sso.new_token_state(cfg)
    resp = JSONResponse({"nonce": nonce})
    set_state_cookie(resp, provider, cookie)
    return resp


@router.post("/auth/sso/{provider}/token")
def sso_token(provider: str, body: TokenBody, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    from .auth import current_sessions, keep_sessions, login_user

    cfg = _token_provider(db, provider)
    saved = sso.unsign(request.cookies.get(state_cookie(provider)), "state")
    if saved is None or saved.get("p") != provider or saved.get("m") != "token":
        raise HTTPException(400, {"code": "state", "message": SSO_TOKEN_MESSAGES["state"]})
    previous = current_sessions(request) if body.add else []
    try:
        claims = sso.id_token_claims(cfg, body.id_token, str(saved.get("n", "")))
        ident = sso.identity_from_claims(cfg, claims)
    except sso.ProviderError as exc:
        log.warning("Anmeldedienst %s (ID-Token): %s", provider, exc)
        raise HTTPException(400, {"code": "provider", "message": SSO_TOKEN_MESSAGES["provider"]}) from None
    except Exception:  # noqa: BLE001
        log.exception("Anmeldedienst %s: ID-Token nicht verarbeitbar", provider)
        raise HTTPException(400, {"code": "provider", "message": SSO_TOKEN_MESSAGES["provider"]}) from None
    problem = sso.domain_problem(cfg, ident)
    res = problem or _authenticate(request, db, cfg, ident)
    if isinstance(res, str):
        raise HTTPException(403 if res != "unknown_user" else 401, {"code": res, "message": res})
    user = res[0]
    resp = JSONResponse({})
    result = login_user(db, user, request, resp, method=cfg.id)
    if previous:
        keep_sessions(db, resp, previous, user.id, request)
    set_hint_cookie(resp, provider, ident.email)
    resp.body = resp.render({**result, "next": safe_next(body.next)})
    resp.headers["content-length"] = str(len(resp.body))
    resp.delete_cookie(state_cookie(provider), path=COOKIE_PATH)      # Nonce nur einmal verwendbar
    return resp


def _link_session(request: Request, db: Session, saved: dict) -> UserSession | None:
    """Sitzung aus dem Status – nur gültig, solange genau diese Sitzung angemeldet ist (Cookie, falls mitgesendet)."""
    try:
        sid, uid = int(saved.get("sid")), int(saved.get("u"))
    except (TypeError, ValueError):
        return None
    sess = db.get(UserSession, sid)
    if sess is None or sess.user_id != uid or sess.expires_at < utcnow():
        return None
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        current = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
        if current is None or current.id != sess.id:
            return None
    elif request.method != "POST":
        return None        # GET-Rückkehr sendet das Sitzungs-Cookie immer mit (SameSite=Lax)
    user = db.get(User, uid)
    return sess if user is not None and user.active else None


def _finish_link(request: Request, db: Session, cfg: sso.ProviderConfig, ident: sso.Identity, saved: dict,
                 session: UserSession) -> RedirectResponse:
    user = db.get(User, session.user_id)
    assert user is not None
    other = db.scalar(select(UserIdentity).where(UserIdentity.provider == cfg.id,
                                                 UserIdentity.subject == ident.subject))
    if other is not None and other.user_id != user.id:
        return _link_error(saved, "already_linked", cfg.id)
    mine = db.scalar(select(UserIdentity).where(UserIdentity.user_id == user.id, UserIdentity.provider == cfg.id))
    if mine is not None and mine.subject and mine.subject != ident.subject:
        return _link_error(saved, "already_connected", cfg.id)
    policy = _policy(db, user)
    if not policy.self_link and cfg.id not in policy.required_links:
        return _link_error(saved, "link_not_allowed", cfg.id)
    if mine is None:
        mine = UserIdentity(user_id=user.id, provider=cfg.id, created_at=utcnow(), created_by=user.id)
        db.add(mine)
    mine.subject = ident.subject
    mine.email = ident.email or mine.email
    mine.email_verified = bool(ident.email_verified) if ident.email else bool(mine.email_verified)
    audit(db, user, "identity.link", f"user:{user.id}",
          {"provider": cfg.id, "via": "profile", "email": ident.email, "mock": cfg.mock}, ip=client_ip(request))
    db.commit()
    target = safe_next(saved.get("nx"), "/profil")
    return _done(RedirectResponse(with_query(target, verbunden=cfg.id), status_code=303), cfg.id)


# =========================================================================== Test-Anbieter (nur Entwicklung)
_MOCK_CSS = """
:root{color-scheme:light dark;--bg:#f6f7f9;--card:#fff;--text:#1d2430;--muted:#5b6575;--line:#d5dae1;--accent:#2457c5;
--warn-bg:#fff4d6;--warn-text:#6b4a00;--err:#b42318}
@media (prefers-color-scheme:dark){:root{--bg:#12161c;--card:#1b2129;--text:#e7ebf0;--muted:#a2acb9;--line:#323b47;
--accent:#7aa2ff;--warn-bg:#3a2f12;--warn-text:#ffd98a;--err:#ff8a80}}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--text)}
main{max-width:26rem;margin:2rem auto;padding:0 16px}
.banner{background:var(--warn-bg);color:var(--warn-text);border:1px solid var(--line);border-radius:8px;
padding:10px 12px;font-weight:600;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px}
h1{font-size:1.3rem;margin:0 0 8px}p{margin:0 0 12px;color:var(--muted)}label{display:block;font-weight:600;margin:12px 0 4px}
input{width:100%;padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--text);font:inherit}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
button{flex:1 1 8rem;padding:10px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);
color:var(--text);font:inherit;cursor:pointer}button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.error{color:var(--err);font-weight:600}
"""


def _mock_page(title: str, body: str, status: int = 200) -> HTMLResponse:
    page = (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
            f"<title>{html.escape(title)}</title><style>{_MOCK_CSS}</style></head><body><main>"
            f'<div class="banner" role="note">Test-Anbieter – nur Entwicklung</div>{body}</main></body></html>')
    return HTMLResponse(page, status_code=status, headers={"Cache-Control": "no-store"})


def _mock_cfg(db: Session, provider: str, client_id: str | None, redirect: str | None) -> sso.ProviderConfig:
    """Nur bei aktivem Test-Anbieter und exakt passender Weiterleitung (kein Open Redirect)."""
    if provider not in PROVIDERS:
        raise HTTPException(404, "Nicht gefunden")
    cfg = sso.resolve(db, provider)
    if not cfg.mock or not sso.mock_enabled():
        raise HTTPException(404, "Nicht gefunden")
    if client_id != sso.MOCK_CLIENT_ID or redirect != sso.redirect_uri(cfg):
        raise HTTPException(400, "Ungültige Anfrage an den Test-Anbieter")
    return cfg


def _hidden(**values: str) -> str:
    return "".join(f'<input type="hidden" name="{k}" value="{html.escape(v or "", quote=True)}">'
                   for k, v in values.items())


def _mock_form(cfg: sso.ProviderConfig, params: dict[str, str], email: str = "", name: str = "",
               error: str | None = None, status: int = 200) -> HTMLResponse:
    label = html.escape(cfg.label)
    err = f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
    body = (f'<div class="card"><h1>Anmelden bei {label} (Test)</h1>'
            f"<p>Hier wird die Anmeldung bei {label} nur simuliert – es wird kein Passwort geprüft. Geben Sie die "
            "E-Mail-Adresse ein, mit der Sie bei diesem Anbieter angemeldet sein möchten.</p>"
            f'{err}<form method="post" action="/api/v1/auth/sso/{cfg.id}/mock">{_hidden(**params)}'
            f'<label for="email">E-Mail-Adresse</label><input id="email" name="email" type="email" required '
            f'autocomplete="email" maxlength="254" value="{html.escape(email, quote=True)}" autofocus>'
            f'<label for="name">Name (optional)</label><input id="name" name="name" type="text" maxlength="200" '
            f'autocomplete="name" value="{html.escape(name, quote=True)}">'
            '<div class="row"><button class="primary" type="submit" name="action" value="login">Anmelden</button>'
            '<button type="submit" name="action" value="cancel" formnovalidate>Abbrechen</button></div>'
            "</form></div>")
    return _mock_page(f"{cfg.label} (Test) – Anmeldung", body, status)


@router.get("/auth/sso/{provider}/mock", include_in_schema=False)
def mock_authorize(provider: str, client_id: str | None = None, redirect_uri: str | None = None,
                   state: str | None = None, nonce: str | None = None, code_challenge: str | None = None,
                   response_mode: str | None = None, db: Session = Depends(get_db)) -> HTMLResponse:
    cfg = _mock_cfg(db, provider, client_id, redirect_uri)
    if not state or not nonce or not code_challenge or max(len(state), len(nonce), len(code_challenge)) > 200:
        raise HTTPException(400, "Ungültige Anfrage an den Test-Anbieter")
    params = {"client_id": client_id or "", "redirect_uri": redirect_uri or "", "state": state, "nonce": nonce,
              "code_challenge": code_challenge, "response_mode": response_mode or ""}
    return _mock_form(cfg, params)


@router.post("/auth/sso/{provider}/mock", include_in_schema=False)
def mock_submit(provider: str, client_id: str = Form("", max_length=100), redirect_uri: str = Form("", max_length=300),
                state: str = Form("", max_length=200), nonce: str = Form("", max_length=200),
                code_challenge: str = Form("", max_length=200), response_mode: str = Form("", max_length=20),
                email: str = Form("", max_length=254), name: str = Form("", max_length=200),
                action: str = Form("login", max_length=20), db: Session = Depends(get_db)):
    cfg = _mock_cfg(db, provider, client_id, redirect_uri)
    if not state or not nonce or not code_challenge:
        raise HTTPException(400, "Ungültige Anfrage an den Test-Anbieter")
    if action == "cancel":
        values = {"error": "access_denied", "state": state}
    else:
        clean = sso.clean_email(email)
        if clean is None:
            params = {"client_id": client_id, "redirect_uri": redirect_uri, "state": state, "nonce": nonce,
                      "code_challenge": code_challenge, "response_mode": response_mode}
            return _mock_form(cfg, params, email, name, "Bitte eine gültige E-Mail-Adresse eingeben.", 422)
        code = sso.issue_mock_code(cfg, email=clean, name=name.strip(), nonce=nonce, challenge=code_challenge)
        values = {"code": code, "state": state}
    if response_mode == "form_post":
        body = (f'<div class="card"><h1>{html.escape(cfg.label)} (Test)</h1>'
                "<p>Der Anbieter schickt die Anmeldung per Formular zurück (wie bei Apple).</p>"
                f'<form method="post" action="{html.escape(redirect_uri, quote=True)}">{_hidden(**values)}'
                f'<div class="row"><button class="primary" type="submit" autofocus>Weiter zum {PRODUCT_NAME}</button>'
                "</div></form></div>")
        return _mock_page(f"{cfg.label} (Test)", body)
    return RedirectResponse(f"{redirect_uri}?{urllib.parse.urlencode(values)}", status_code=303)


# =========================================================================== Angemeldet: eigene Verknüpfungen
class LinkBody(BaseModel):
    next: str | None = Field(default=None, max_length=500)


def _unlink_problem(db: Session, user: User, provider: str, policy, rows: dict, available: dict) -> dict | None:
    if not policy.self_link:
        return {"code": "link_not_allowed", "message": "Verbundene Konten werden von der Schule verwaltet."}
    if provider in policy.required_links:
        return {"code": "required", "message": "Diese Verknüpfung ist für Ihr Konto Pflicht."}
    if user.password_hash and "password" in policy.methods:
        return None
    for pid, row in rows.items():
        if pid != provider and row.subject and pid in available and pid in policy.methods:
            return None
    return {"code": "last_method",
            "message": "Ohne diese Verknüpfung hätten Sie keinen erlaubten Anmeldeweg mehr."}


def _me_view(db: Session, user: User) -> dict[str, Any]:
    policy = _policy(db, user)
    rows = {r.provider: r for r in identity_rows(db, user.id)}
    available = {p["id"]: p for p in available_providers(db)}
    providers = []
    for pid in PROVIDERS:
        row, av = rows.get(pid), available.get(pid)
        required = pid in policy.required_links
        if row is None and av is None and not required:
            continue
        linked = row is not None and row.subject is not None
        problem = _unlink_problem(db, user, pid, policy, rows, available) if linked else None
        label = av["label"] if av else _label(db, pid)
        providers.append({
            "id": pid, "label": label, "mock": bool(av and av["mock"]), "available": av is not None,
            "required": required, "linked": linked, "identity": public_identity(row, label) if row else None,
            "can_link": av is not None and not linked and (policy.self_link or required),
            "can_unlink": linked and problem is None, "unlink_block": problem,
        })
    return {"providers": providers, "linked": [p for p in PROVIDERS if p in rows and rows[p].subject],
            "available": list(available.values()), "required": [p for p in PROVIDERS if p in policy.required_links],
            "self_link": bool(policy.self_link), "methods": sorted(policy.methods)}


def _me_row(db: Session, user: AuthUser) -> User:
    row = db.get(User, user.id)
    if row is None:
        raise HTTPException(401, "not_authenticated")
    return row


@router.get("/me/identities")
def my_identities(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return _me_view(db, _me_row(db, user))


@router.post("/me/identities/{provider}/link")
def link_start(provider: str, request: Request, body: LinkBody | None = None,
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> JSONResponse:
    """Verbinden starten → ``{url}`` (Browser dorthin schicken). Nur in einer angemeldeten Sitzung."""
    _known(provider)
    if user.auth_method != "session" or not user.session_id:
        raise HTTPException(403, "Nur mit angemeldeter Sitzung möglich")
    row = _me_row(db, user)
    cfg = sso.resolve(db, provider)
    if not cfg.usable:
        raise HTTPException(409, {"code": "provider_disabled", "message": f"{cfg.label} ist nicht eingerichtet."})
    policy = _policy(db, row)
    if not policy.self_link and provider not in policy.required_links:
        raise HTTPException(403, {"code": "link_not_allowed",
                                  "message": "Verbundene Konten werden von der Schule verwaltet."})
    mine = db.scalar(select(UserIdentity).where(UserIdentity.user_id == row.id, UserIdentity.provider == provider))
    if mine is not None and mine.subject:
        raise HTTPException(409, {"code": "already_connected",
                                  "message": f"Ihr Konto ist bereits mit {cfg.label} verbunden."})
    try:
        url, cookie = sso.new_flow(cfg, mode="link", next_path=safe_next(body.next if body else None, "/profil"),
                                   user_id=row.id, session_id=user.session_id)
    except Exception:  # noqa: BLE001
        log.exception("Anmeldedienst %s: Verbinden konnte nicht starten", provider)
        raise HTTPException(502, {"code": "provider", "message": f"{cfg.label} ist gerade nicht erreichbar."}) \
            from None
    resp = JSONResponse({"url": url})
    set_state_cookie(resp, provider, cookie)
    return resp


@router.delete("/me/identities/{provider}")
def unlink_mine(provider: str, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    _known(provider)
    if user.auth_method != "session":
        raise HTTPException(403, "Nur mit angemeldeter Sitzung möglich")
    row = _me_row(db, user)
    rows = {r.provider: r for r in identity_rows(db, row.id)}
    ident = rows.get(provider)
    if ident is None or not ident.subject:
        raise HTTPException(404, "Dieses Konto ist nicht verbunden.")
    available = {p["id"]: p for p in available_providers(db)}
    problem = _unlink_problem(db, row, provider, _policy(db, row), rows, available)
    if problem:
        raise HTTPException(403 if problem["code"] == "link_not_allowed" else 409, problem)
    _remove(db, row, ident)
    audit(db, user, "identity.unlink", f"user:{row.id}", {"provider": provider}, ip=client_ip(request))
    db.commit()
    return _me_view(db, row)


def _remove(db: Session, user: User, ident: UserIdentity) -> None:
    if ident.provider == "oidc" and ident.subject and user.oidc_sub == ident.subject:
        user.oidc_sub = None          # alte Verknüpfung (vor §11.4) mit entfernen
    db.delete(ident)
    db.flush()


# =========================================================================== Verwaltung: Verknüpfungen eines Kontos
class ReserveBody(BaseModel):
    provider: str = Field(max_length=20)
    email: str = Field(max_length=254)


def _target(db: Session, actor: AuthUser, user_id: int) -> User:
    from .users import _check_manage, _get

    target = _get(db, user_id)
    _check_manage(actor, target.role)
    return target


def _admin_view(db: Session, target: User) -> dict[str, Any]:
    policy = _policy(db, target)
    available = {p["id"]: p for p in available_providers(db)}
    return {
        "items": [public_identity(r, _label(db, r.provider)) for r in identity_rows(db, target.id)],
        "providers": [{"id": pid, "label": available[pid]["label"] if pid in available else _label(db, pid),
                       "available": pid in available, "mock": bool(pid in available and available[pid]["mock"]),
                       "required": pid in policy.required_links} for pid in PROVIDERS],
        "required": [p for p in PROVIDERS if p in policy.required_links],
        "self_link": bool(policy.self_link),
    }


@router.get("/users/{user_id}/identities")
def user_identities(user_id: int, actor: AuthUser = Depends(require("users.manage")),
                    db: Session = Depends(get_db)) -> dict:
    return _admin_view(db, _target(db, actor, user_id))


@router.post("/users/{user_id}/identities", status_code=201)
def reserve_identity(user_id: int, body: ReserveBody, request: Request,
                     actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    """E-Mail vormerken: beim ersten Anmelden mit dieser, vom Anbieter bestätigten Adresse wird verbunden."""
    target = _target(db, actor, user_id)
    provider = _known(body.provider)
    email = sso.clean_email(body.email)
    if email is None:
        raise HTTPException(422, "Bitte eine gültige E-Mail-Adresse angeben.")
    row = db.scalar(select(UserIdentity).where(UserIdentity.user_id == target.id, UserIdentity.provider == provider))
    if row is not None and row.subject:
        raise HTTPException(409, f"Das Konto ist bereits mit {_label(db, provider)} verbunden – zuerst lösen.")
    clash = db.scalar(select(UserIdentity.id).where(UserIdentity.provider == provider,
                                                    UserIdentity.subject.is_(None),
                                                    func.lower(UserIdentity.email) == email,
                                                    UserIdentity.user_id != target.id))
    if clash is not None:
        raise HTTPException(409, "Diese Adresse ist für diesen Anbieter bereits bei einem anderen Konto vorgemerkt.")
    if row is None:
        row = UserIdentity(user_id=target.id, provider=provider, created_at=utcnow(), created_by=actor.id)
        db.add(row)
    row.email, row.email_verified, row.created_by = email, False, actor.id
    audit(db, actor, "identity.reserve", f"user:{target.id}", {"provider": provider, "email": email},
          ip=client_ip(request))
    db.commit()
    return _admin_view(db, target)


@router.delete("/users/{user_id}/identities/{provider}")
def remove_identity(user_id: int, provider: str, request: Request,
                    actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    target = _target(db, actor, user_id)
    _known(provider)
    row = db.scalar(select(UserIdentity).where(UserIdentity.user_id == target.id, UserIdentity.provider == provider))
    if row is None:
        raise HTTPException(404, "Keine Verknüpfung mit diesem Anbieter.")
    linked = row.subject is not None
    _remove(db, target, row)
    audit(db, actor, "identity.admin_unlink", f"user:{target.id}", {"provider": provider, "linked": linked},
          ip=client_ip(request))
    db.commit()
    return _admin_view(db, target)


# =========================================================================== Einrichtung (nur Administration)
def require_admin(user: AuthUser = Depends(current_user)) -> AuthUser:
    if user.role != "admin":
        raise HTTPException(403, "Anmeldedienste kann nur die Administration einrichten.")
    return user


class ProviderBody(BaseModel):
    enabled: bool | None = None
    auto_signin: bool | None = None
    client_id: str | None = Field(default=None, max_length=255)
    client_secret: str | None = Field(default=None, max_length=4096)   # leer/None = unverändert
    clear_client_secret: bool = False
    tenant: str | None = Field(default=None, max_length=100)
    hosted_domain: str | None = Field(default=None, max_length=255)
    team_id: str | None = Field(default=None, max_length=20)
    key_id: str | None = Field(default=None, max_length=20)
    private_key: str | None = Field(default=None, max_length=10000)     # leer/None = unverändert
    clear_private_key: bool = False
    issuer: str | None = Field(default=None, max_length=500)
    label: str | None = Field(default=None, max_length=100)
    allowed_domains: list[str] | None = Field(default=None, max_length=50)


_DOMAIN = re.compile(r"^(?=.{1,253}$)[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$")
_TENANT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,99}$")
_APPLE_ID = re.compile(r"^[A-Za-z0-9]{1,20}$")
_CLIENT_ID = re.compile(r"^[\x21-\x7e]{1,255}$")


#: Art der automatischen Anmeldung je Anbieter (Anzeige in den Einstellungen)
AUTO_KIND = {"google": "one_tap", "microsoft": "silent"}


def _origin() -> str:
    parts = urllib.parse.urlsplit(config.base_url)
    return f"{parts.scheme}://{parts.netloc}"


def _warnings(provider: str) -> list[str]:
    """Hinweise zur eigenen Adresse (``SM_BASE_URL``), die für den Anbieter ein Problem sein können."""
    parts = urllib.parse.urlsplit(config.base_url)
    out: list[str] = []
    default_port = 443 if parts.scheme == "https" else 80
    if provider == "apple":
        if parts.port not in (None, default_port):
            out.append(f"Apple akzeptiert für „Sign in with Apple“ keine Adressen mit Port (hier :{parts.port}); laut "
                       "Apple-Entwicklerforum sind Ports und localhost nicht unterstützt. Es braucht eine Adresse "
                       "auf Port 443 (z. B. Reverse-Proxy oder eine eigene Subdomain).")
        if parts.scheme != "https":
            out.append("Apple verlangt https.")
    if provider in ("google", "microsoft") and parts.scheme != "https"             and parts.hostname not in ("localhost", "127.0.0.1"):
        out.append("Google und Microsoft verlangen für echte Adressen https.")
    if provider == "google" and parts.port not in (None, default_port):
        out.append(f"Die Adresse hat einen Port (:{parts.port}). Google dokumentiert Ports bei den „Autorisierten "
                   "JavaScript-Quellen“ nur für Entwicklung – bitte nach dem Eintragen mit „Verbindung testen“ und "
                   "einer Probeanmeldung prüfen.")
    return out


def _provider_view(db: Session, provider: str) -> dict[str, Any]:
    cfg = sso.resolve(db, provider)
    row = db.get(SsoProvider, provider)
    stored = {"client_id": row.client_id, "tenant": row.tenant, "hosted_domain": row.hosted_domain,
              "team_id": row.team_id, "key_id": row.key_id, "issuer": row.issuer, "label": row.label} if row else {}
    effective = {"client_id": cfg.client_id, "tenant": cfg.tenant, "hosted_domain": cfg.hosted_domain,
                 "team_id": cfg.team_id, "key_id": cfg.key_id, "issuer": cfg.issuer,
                 "label": cfg.label if cfg.label != sso.DEFAULT_LABELS[provider] else None}
    fields = {}
    for name in sso.FIELDS[provider]:
        if name in sso.SECRET_FIELDS:
            continue
        if name == "allowed_domains":
            fields[name] = list(cfg.allowed_domains)
        else:
            fields[name] = (effective if name in cfg.env_fields else stored).get(name) or ""
    status = "active" if cfg.enabled else "mock" if cfg.mock else "disabled" if cfg.configured else "missing"
    return {
        "id": provider, "label": cfg.label, "default_label": sso.DEFAULT_LABELS[provider], "status": status,
        "enabled": cfg.enabled, "configured": cfg.configured, "db_enabled": cfg.db_enabled, "mock": cfg.mock,
        "auto_signin": cfg.auto_signin, "auto_kind": AUTO_KIND.get(provider),
        "origin": _origin(), "js_origins": [_origin()] if provider in ("google", "apple") else [],
        "warnings": _warnings(provider),
        "script_hosts": sorted({src for srcs in sso.CSP_BY_PROVIDER.get(provider, {}).values() for src in srcs}),
        "fields": fields, "field_names": list(sso.FIELDS[provider]), "required": list(sso.REQUIRED[provider]),
        "missing": list(cfg.missing), "secrets": {k: v for k, v in cfg.secrets_set.items()
                                                  if k in sso.FIELDS[provider]},
        "env_fields": sorted(cfg.env_fields),
        "env_vars": {k: v for k, v in sso.ENV_VARS[provider].items()},
        "redirect_uri": sso.setup_redirect_uri(provider),
        "updated_at": iso(row.updated_at) if row else None,
    }


@router.get("/sso/providers/config")
def provider_config(actor: AuthUser = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return {"providers": [_provider_view(db, p) for p in PROVIDERS], "mock_enabled": sso.mock_enabled(),
            "production": config.is_production, "base_url": config.base_url,
            "field_labels": sso.FIELD_LABELS}


def _clean_field(name: str, value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if name == "client_id" and not _CLIENT_ID.match(value):
        raise HTTPException(422, "Die Client-ID enthält ungültige Zeichen.")
    if name == "tenant" and not _TENANT.match(value):
        raise HTTPException(422, "Mandant: Tenant-ID (GUID), Domain oder „organizations“/„common“ angeben.")
    if name == "hosted_domain" and not _DOMAIN.match(value.lower()):
        raise HTTPException(422, "Bitte eine gültige Domain angeben (z. B. schule.de).")
    if name in ("team_id", "key_id") and not _APPLE_ID.match(value):
        raise HTTPException(422, f"{sso.FIELD_LABELS[name]}: nur Buchstaben und Ziffern (z. B. ABCDE12345).")
    if name == "issuer":
        parts = urllib.parse.urlsplit(value)
        ok = parts.scheme == "https" or (parts.scheme == "http" and config.is_development)
        if not ok or not parts.netloc or parts.query or parts.fragment:
            raise HTTPException(422, "Aussteller: vollständige https-Adresse ohne Parameter angeben.")
        value = value.rstrip("/")
        problem = net_guard.validate_url(value, "oidc")
        if problem:
            raise HTTPException(422, f"Aussteller: {problem}")
    return value.lower() if name == "hosted_domain" else value


@router.put("/sso/providers/{provider}")
def update_provider(provider: str, body: ProviderBody, request: Request, actor: AuthUser = Depends(require_admin),
                    db: Session = Depends(get_db)) -> dict:
    from .. import crypto

    _known(provider)
    allowed = set(sso.FIELDS[provider])
    row = db.get(SsoProvider, provider)
    if row is None:
        row = SsoProvider(provider=provider, enabled=False, updated_at=utcnow())
        db.add(row)
    changed: list[str] = []
    for name in ("client_id", "tenant", "hosted_domain", "team_id", "key_id", "issuer", "label"):
        value = getattr(body, name)
        if name in allowed and value is not None:
            clean = _clean_field(name, value)
            if getattr(row, name) != clean:
                setattr(row, name, clean)
                changed.append(name)
    if "allowed_domains" in allowed and body.allowed_domains is not None:
        domains = sorted({d.strip().lower().lstrip("@") for d in body.allowed_domains if d.strip()})
        bad = [d for d in domains if not _DOMAIN.match(d)]
        if bad:
            raise HTTPException(422, f"Ungültige Domain: {', '.join(bad[:5])}")
        if (row.allowed_domains or []) != domains:
            row.allowed_domains = domains or None
            changed.append("allowed_domains")
    if "client_secret" in allowed:
        if body.clear_client_secret:
            if row.client_secret_enc:
                row.client_secret_enc = None
                changed.append("client_secret")
        elif body.client_secret and body.client_secret.strip():
            row.client_secret_enc = crypto.encrypt_text(body.client_secret.strip(),
                                                        sso.secret_aad(provider, "client_secret"))
            changed.append("client_secret")
    if "private_key" in allowed:
        if body.clear_private_key:
            if row.private_key_enc:
                row.private_key_enc = None
                changed.append("private_key")
        elif body.private_key and body.private_key.strip():
            pem = body.private_key.strip().replace("\\n", "\n")
            try:
                sso.load_apple_key(pem)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from None
            row.private_key_enc = crypto.encrypt_text(pem, sso.secret_aad(provider, "private_key"))
            changed.append("private_key")
    if body.auto_signin is not None and bool(row.auto_signin) != body.auto_signin:
        row.auto_signin = body.auto_signin
        changed.append("auto_signin")
    if body.enabled is not None and bool(row.enabled) != body.enabled:
        row.enabled = body.enabled
        changed.append("enabled")
    db.flush()
    cfg = sso.resolve(db, provider)
    if row.enabled and not cfg.configured:
        db.rollback()
        missing = ", ".join(sso.FIELD_LABELS.get(m, m) for m in cfg.missing)
        raise HTTPException(422, f"Zum Einschalten fehlen noch: {missing}.")
    row.updated_at, row.updated_by = utcnow(), actor.id
    audit(db, actor, "sso_provider.update", f"sso:{provider}", {"changed": changed, "enabled": bool(row.enabled)},
          ip=client_ip(request))
    db.commit()
    sso.clear_cache(cfg)
    return _provider_view(db, provider)


@router.post("/sso/providers/{provider}/test")
def test_provider(provider: str, actor: AuthUser = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    """Verbindung prüfen: Discovery abrufen (Apple: Schlüssel/Client-Secret erzeugen + Apple-Discovery)."""
    _known(provider)
    cfg = sso.resolve(db, provider)
    if not cfg.configured:
        missing = ", ".join(sso.FIELD_LABELS.get(m, m) for m in cfg.missing)
        return {"ok": False, "message": f"Noch nicht vollständig eingerichtet – es fehlen: {missing}."}
    try:
        sso.clear_cache(cfg)
        if provider == "apple":
            sso.apple_client_secret(cfg)
            meta = sso.discovery(sso.APPLE_ISSUER)
        else:
            meta = sso.metadata(cfg)
        if provider in ("google", "apple", "microsoft"):
            keys = sso.fetch_jwks(sso.jwks_uri(cfg, meta), force=True).get("keys") or []
            if not keys:
                return {"ok": False, "message": "Der Anbieter liefert keine Signaturschlüssel (JWKS)."}
    except (sso.ProviderError, ValueError) as exc:
        return {"ok": False, "message": f"Fehler: {str(exc)[:300]}"}
    except Exception as exc:  # noqa: BLE001 – Netzwerkfehler usw. als Meldung zurückgeben
        log.warning("Anmeldedienst %s: Verbindungstest fehlgeschlagen: %s", provider, exc)
        return {"ok": False, "message": "Anbieter nicht erreichbar oder Adresse nicht zulässig."}
    return {"ok": True, "message": "Verbindung erfolgreich – der Anbieter ist erreichbar.",
            "issuer": meta.get("issuer"), "jwks_ok": provider in ("google", "apple", "microsoft"),
            "authorization_endpoint": meta.get("authorization_endpoint"),
            "token_endpoint": meta.get("token_endpoint"),
            "note": None if cfg.enabled else "Der Anbieter ist eingerichtet, aber noch nicht eingeschaltet."}
