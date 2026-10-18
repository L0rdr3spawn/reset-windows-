"""Anmeldedienste Microsoft, Apple, Google und Schulkonto (OIDC) – docs/ARCHITECTURE.md §11.4.

Registry + Protokoll (Authorization Code Flow + PKCE + nonce, nur Standardbibliothek und ``cryptography``):

* :func:`resolve` – wirksame Einrichtung eines Anbieters. **Umgebungsvariablen haben Vorrang** vor der Einrichtung im
  Admin-Bereich (Tabelle ``sso_providers``, Geheimnisse verschlüsselt): ``SM_SSO_MICROSOFT_CLIENT_ID/_SECRET/_TENANT``
  (Standard ``organizations``), ``SM_SSO_GOOGLE_CLIENT_ID/_SECRET/_HD``, ``SM_SSO_APPLE_CLIENT_ID`` (Services-ID)
  ``/_TEAM_ID/_KEY_ID/_PRIVATE_KEY`` (PEM-Inhalt oder Dateipfad), ``SM_OIDC_*`` → Anbieter ``oidc``.
* **Test-Anbieter** (``SM_SSO_DEV_MOCK``, nie in Produktion): nicht eingerichtete Anbieter melden über eine interne
  Seite an; der Token-Austausch löst den signierten Test-Code lokal auf – danach derselbe Code-Pfad.
* :func:`metadata` – Endpunkte (Discovery mit 1 h Cache; Apple fest), :func:`authorization_url`,
  :func:`fetch_claims` (Code → ID-Token direkt per TLS vom Token-Endpunkt; laut OIDC Core 3.1.3.7 ersetzt die
  TLS-Prüfung dort die Signaturprüfung; geprüft werden ``iss``, ``aud``/``azp``, ``exp``, ``nonce``, ``sub``),
  :func:`identity_from_claims` (Kennung, E-Mail, „E-Mail bestätigt“ je Anbieter).
* Microsoft: Aussteller-Vorlage ``{tenantid}`` wird gegen den ``tid``-Claim geprüft; die E-Mail gilt nur als bestätigt,
  wenn sie aus ``preferred_username`` (UPN – Domain im Mandanten verifiziert) stammt, ``xms_edov`` gesetzt ist oder ein
  fester Mandant eingetragen ist (das frei setzbare ``mail``-Attribut fremder Mandanten zählt nicht).
* Apple: ``response_mode=form_post`` (Callback per POST), Client-Secret als ES256-JWT (:func:`apple_client_secret`),
  ``email_verified`` kann ein String sein, private Relay-Adressen werden normal behandelt; Apple dokumentiert kein PKCE.
* **Direkte ID-Tokens aus dem Browser** (Google Identity Services / One Tap, Sign in with Apple JS im Popup):
  :func:`id_token_claims` prüft hier zusätzlich die **Signatur über JWKS** (nur RS256, ``kid``, Schlüsselsatz 1 h
  gecacht), dann ``iss``, ``aud``/``azp``, ``exp``, ``nonce`` (an den Status-Cookie gebunden) und ``sub``.
* :func:`csp_sources` – Quellen für die Content-Security-Policy, nur für **aktive** Anbieter (nichts vorab).
* **Direkte ID-Tokens aus dem Browser** (Google Identity Services / One Tap, Sign in with Apple JS im Popup):
  :func:`id_token_claims` prüft zusätzlich die **Signatur über JWKS** (nur RS256, ``kid``, Schlüsselsatz 1 h
  gecacht), dann ``iss``, ``aud``/``azp``, ``exp``, ``nonce`` (an den Status-Cookie gebunden) und ``sub``.
* :func:`csp_sources` – Quellen für die Content-Security-Policy, nur für **aktive** Anbieter (nichts vorab).
* Alle HTTP-Abrufe laufen über :func:`http_json` → ``_http_json`` (in Tests ersetzbar, hier oder – wie bisher – in
  ``routes.oidc``).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import net_guard
from .config import config

log = logging.getLogger("schulmanager.sso")

API = "/api/v1"
PROVIDERS: tuple[str, ...] = ("microsoft", "apple", "google", "oidc")
DEFAULT_LABELS: dict[str, str] = {"microsoft": "Microsoft", "apple": "Apple", "google": "Google", "oidc": "Schulkonto"}
FORM_POST = frozenset({"apple"})           # Callback per POST (response_mode=form_post)
NO_PKCE = frozenset({"apple"})             # Apple dokumentiert kein PKCE (vertrauliche Clients mit JWT-Secret)

MS_DEFAULT_TENANT = "organizations"
MS_MULTI_TENANT = frozenset({"common", "organizations", "consumers"})
MS_AUTHORITY = "https://login.microsoftonline.com"
GOOGLE_ISSUER = "https://accounts.google.com"
APPLE_ISSUER = "https://appleid.apple.com"
APPLE_AUTHORIZE = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN = "https://appleid.apple.com/auth/token"
APPLE_SECRET_MAX = 180 * 86400             # Apple: Client-Secret höchstens 6 Monate gültig

MOCK_CLIENT_ID = "schulmanager-test"
MOCK_TOKEN_ENDPOINT = "mock:token"
MOCK_TENANT = "00000000-0000-4000-8000-000000000000"
MOCK_CODE_TTL = 120
STATE_TTL = 600
DISCOVERY_TTL = 3600

# Felder je Anbieter (Einrichtung) und Pflichtfelder für „eingerichtet“
FIELDS: dict[str, tuple[str, ...]] = {
    "microsoft": ("client_id", "client_secret", "tenant", "label", "allowed_domains"),
    "google": ("client_id", "client_secret", "hosted_domain", "label", "allowed_domains"),
    "apple": ("client_id", "team_id", "key_id", "private_key", "label", "allowed_domains"),
    "oidc": ("issuer", "client_id", "client_secret", "label", "allowed_domains"),
}
REQUIRED: dict[str, tuple[str, ...]] = {
    "microsoft": ("client_id", "client_secret"),
    "google": ("client_id", "client_secret"),
    "apple": ("client_id", "team_id", "key_id", "private_key"),
    "oidc": ("issuer", "client_id"),
}
FIELD_LABELS: dict[str, str] = {
    "client_id": "Client-ID", "client_secret": "Client-Secret", "tenant": "Mandant (Tenant)",
    "hosted_domain": "Google-Workspace-Domain", "team_id": "Team-ID", "key_id": "Schlüssel-ID",
    "private_key": "Privater Schlüssel (.p8)", "issuer": "Aussteller (Issuer-URL)", "label": "Bezeichnung",
    "allowed_domains": "Erlaubte E-Mail-Domains",
}
# Umgebungsvariablen je Feld (Vorrang vor der Datenbank)
ENV_VARS: dict[str, dict[str, str]] = {
    "microsoft": {"client_id": "SM_SSO_MICROSOFT_CLIENT_ID", "client_secret": "SM_SSO_MICROSOFT_CLIENT_SECRET",
                  "tenant": "SM_SSO_MICROSOFT_TENANT"},
    "google": {"client_id": "SM_SSO_GOOGLE_CLIENT_ID", "client_secret": "SM_SSO_GOOGLE_CLIENT_SECRET",
               "hosted_domain": "SM_SSO_GOOGLE_HD"},
    "apple": {"client_id": "SM_SSO_APPLE_CLIENT_ID", "team_id": "SM_SSO_APPLE_TEAM_ID",
              "key_id": "SM_SSO_APPLE_KEY_ID", "private_key": "SM_SSO_APPLE_PRIVATE_KEY"},
    "oidc": {"issuer": "SM_OIDC_ISSUER", "client_id": "SM_OIDC_CLIENT_ID", "client_secret": "SM_OIDC_CLIENT_SECRET",
             "label": "SM_OIDC_LABEL"},
}
SECRET_FIELDS = frozenset({"client_secret", "private_key"})

_discovery: dict[str, tuple[float, dict]] = {}     # issuer → (gültig bis, Metadaten); geteilt mit routes.oidc
_used_mock_codes: dict[str, float] = {}


class ProviderError(RuntimeError):
    """Fehler beim Anbieter (Discovery, Token-Austausch, ungültiges ID-Token)."""


# =========================================================================== Einrichtung
@dataclass
class ProviderConfig:
    id: str
    label: str
    configured: bool = False             # alle Pflichtfelder vorhanden
    enabled: bool = False                # eingerichtet UND eingeschaltet (Umgebung = immer eingeschaltet)
    mock: bool = False                   # Test-Anbieter statt echter Anmeldung
    client_id: str | None = None
    client_secret: str | None = None
    tenant: str | None = None
    hosted_domain: str | None = None
    team_id: str | None = None
    key_id: str | None = None
    private_key: str | None = None
    issuer: str | None = None
    allowed_domains: tuple[str, ...] = ()
    env_fields: frozenset[str] = frozenset()
    missing: tuple[str, ...] = ()
    db_enabled: bool = False
    auto_signin: bool = False            # automatische Anmeldung (Google One Tap mit Auto-Auswahl, Microsoft still)
    secrets_set: dict[str, bool] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.enabled or self.mock

    @property
    def form_post(self) -> bool:
        return self.id in FORM_POST

    @property
    def pkce(self) -> bool:
        return self.mock or self.id not in NO_PKCE


def mock_enabled() -> bool:
    """Test-Anbieter erlaubt? Nur mit ausdrücklichem ``SM_SSO_DEV_MOCK=1`` **und** Entwicklung (``SM_ENV=development``);
    nie in Produktion und nie in der Demo (``config.validate`` verbietet die Kombination zusätzlich beim Start)."""
    return (bool(config.sso_dev_mock) and config.env == "development" and not config.is_production
            and not config.demo_public and config.mode != "demo")


def _load_pem(value: str | None) -> str | None:
    """PEM-Inhalt (auch mit ``\\n``-Escapes) oder Pfad zu einer ``.p8``-Datei."""
    if not value:
        return None
    text = value.strip()
    if "-----BEGIN" in text:
        return text.replace("\\n", "\n")
    try:
        return Path(text).expanduser().read_text(encoding="utf-8")
    except (OSError, ValueError):
        # Wert nie protokollieren – es könnte der Schlüssel selbst sein (z. B. PEM ohne „-----BEGIN“-Zeile)
        log.error("Apple-Schlüssel nicht lesbar (SM_SSO_APPLE_PRIVATE_KEY: PEM-Inhalt oder Pfad zu einer .p8-Datei)")
        return None


def _env_values(provider: str) -> dict[str, Any]:
    if provider == "microsoft":
        values = {"client_id": config.sso_microsoft_client_id, "client_secret": config.sso_microsoft_client_secret,
                  "tenant": config.sso_microsoft_tenant}
    elif provider == "google":
        values = {"client_id": config.sso_google_client_id, "client_secret": config.sso_google_client_secret,
                  "hosted_domain": config.sso_google_hd}
    elif provider == "apple":
        values = {"client_id": config.sso_apple_client_id, "team_id": config.sso_apple_team_id,
                  "key_id": config.sso_apple_key_id, "private_key": _load_pem(config.sso_apple_private_key)}
    elif provider == "oidc":
        label = config.oidc_label if config.oidc_label and config.oidc_label != "Single Sign-on" else None
        values = {"issuer": config.oidc_issuer, "client_id": config.oidc_client_id,
                  "client_secret": config.oidc_client_secret, "label": label}
    else:
        values = {}
    return {k: v for k, v in values.items() if v}


def secret_aad(provider: str, name: str) -> str:
    return f"sso_providers.{name}:{provider}"


def _row_values(row) -> dict[str, Any]:
    """Werte aus der Tabelle ``sso_providers`` (Geheimnisse entschlüsselt)."""
    from . import crypto

    if row is None:
        return {}
    values: dict[str, Any] = {"client_id": row.client_id, "tenant": row.tenant, "hosted_domain": row.hosted_domain,
                              "team_id": row.team_id, "key_id": row.key_id, "issuer": row.issuer, "label": row.label,
                              "allowed_domains": row.allowed_domains}
    for name, column in (("client_secret", "client_secret_enc"), ("private_key", "private_key_enc")):
        token = getattr(row, column)
        if token:
            try:
                values[name] = crypto.decrypt_text(token, secret_aad(row.provider, name))
            except Exception:  # noqa: BLE001 – falscher Schlüssel: als „nicht gesetzt“ behandeln, nicht abstürzen
                log.error("Geheimnis %s des Anbieters %s nicht entschlüsselbar", name, row.provider)
    return {k: v for k, v in values.items() if v}


def resolve(db, provider: str) -> ProviderConfig:
    """Wirksame Einrichtung (Umgebung vor Datenbank). ``db`` darf ``None`` sein (nur Umgebung)."""
    if provider not in PROVIDERS:
        raise KeyError(provider)
    row = None
    if db is not None:
        from .feature_models.identities import SsoProvider

        try:
            row = db.get(SsoProvider, provider)
        except Exception:  # noqa: BLE001 – Tabelle fehlt (alte Datenbank): nur Umgebung
            log.exception("Tabelle sso_providers nicht lesbar")
            row = None
    env = _env_values(provider)
    stored = _row_values(row)
    merged = {**stored, **env}
    domains = tuple(sorted({str(d).strip().lower() for d in (merged.get("allowed_domains") or []) if str(d).strip()}))
    missing = tuple(f for f in REQUIRED[provider] if not merged.get(f))
    configured = not missing
    env_enabled = any(f in env for f in REQUIRED[provider] if f != "client_secret")
    db_enabled = bool(row is not None and row.enabled)
    enabled = configured and (env_enabled or db_enabled)
    cfg = ProviderConfig(
        id=provider, label=str(merged.get("label") or DEFAULT_LABELS[provider]), configured=configured,
        enabled=enabled, mock=mock_enabled() and not configured and provider != "oidc",
        client_id=merged.get("client_id"), client_secret=merged.get("client_secret"),
        tenant=merged.get("tenant") or (MS_DEFAULT_TENANT if provider == "microsoft" else None),
        hosted_domain=(merged.get("hosted_domain") or "").lower() or None, team_id=merged.get("team_id"),
        key_id=merged.get("key_id"), private_key=merged.get("private_key"), issuer=merged.get("issuer"),
        allowed_domains=domains, env_fields=frozenset(env), missing=missing, db_enabled=db_enabled,
        auto_signin=bool(row is not None and row.auto_signin),
        secrets_set={"client_secret": bool(merged.get("client_secret")),
                     "private_key": bool(merged.get("private_key"))})
    return cfg


def redirect_uri(cfg: ProviderConfig, *, absolute: bool = True) -> str:
    """Weiterleitungs-URI (beim Anbieter einzutragen). Schulkonto: weiter der alte Pfad ``/auth/oidc/callback``.

    Der Test-Anbieter nutzt relative Adressen – so funktioniert er auch hinter Vorschau-Proxys ohne ``SM_BASE_URL``.
    """
    path = f"{API}/auth/oidc/callback" if cfg.id == "oidc" and not cfg.mock else f"{API}/auth/sso/{cfg.id}/callback"
    return path if cfg.mock or not absolute else f"{config.base_url}{path}"


def setup_redirect_uri(provider: str) -> str:
    return f"{config.base_url}{API}/auth/oidc/callback" if provider == "oidc" \
        else f"{config.base_url}{API}/auth/sso/{provider}/callback"


# =========================================================================== HTTP, Discovery
def _http_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    """GET (bzw. POST bei ``data``, form-encoded) und JSON-Antwort. In Tests ersetzbar."""
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Accept": "application/json", **(headers or {})})
    try:
        with net_guard.urlopen(req, "oidc", timeout=10) as resp:     # Zielprüfung gegen SSRF, keine Weiterleitungen
            return json.loads(resp.read(1_000_000).decode("utf-8"))
    except net_guard.BlockedTarget:
        raise ProviderError("Diese Adresse ist nicht zulässig (nur öffentliche https-Adressen; interne Dienste "
                            "muss die Administration freigeben).") from None
    except urllib.error.HTTPError as exc:
        # Antwortinhalt nie an Nutzer weitergeben (blinder/lesender SSRF)
        raise ProviderError(f"HTTP {exc.code} von {urllib.parse.urlsplit(url).netloc}") from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, net_guard.BlockedTarget):
            raise ProviderError("Diese Adresse ist nicht zulässig (nur öffentliche https-Adressen; interne Dienste "
                                "muss die Administration freigeben).") from None
        raise ProviderError(f"{urllib.parse.urlsplit(url).netloc} ist nicht erreichbar") from None
    except (ValueError, OSError):
        raise ProviderError(f"Ungültige Antwort von {urllib.parse.urlsplit(url).netloc}") from None


def http_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    """Alle Abrufe beim Anbieter. Tests ersetzen ``_http_json`` hier oder in ``routes.oidc`` (ältere Tests)."""
    fn = _http_json
    try:
        from .routes import oidc as legacy

        candidate = getattr(legacy, "_http_json", None)
        if candidate is not None and not getattr(candidate, "_sm_delegate", False):
            fn = candidate
    except ImportError:  # pragma: no cover
        pass
    return fn(url, data, headers)


def _check_endpoint(url: Any, what: str) -> str:
    if not isinstance(url, str) or not url:
        raise ProviderError(f"Discovery ohne {what}")
    if not url.startswith("https://") and not (config.is_development and url.startswith("http://")):
        raise ProviderError(f"{what} muss https:// verwenden")
    return url


def discovery(issuer: str) -> dict:
    issuer = issuer.rstrip("/")
    cached = _discovery.get(issuer)
    if cached and cached[0] > time.time():
        return cached[1]
    meta = http_json(f"{issuer}/.well-known/openid-configuration")
    if not isinstance(meta, dict):
        raise ProviderError("Discovery-Antwort ist kein JSON-Objekt")
    _check_endpoint(meta.get("authorization_endpoint"), "authorization_endpoint")
    _check_endpoint(meta.get("token_endpoint"), "token_endpoint")
    _discovery[issuer] = (time.time() + DISCOVERY_TTL, meta)
    return meta


def discovery_issuer(cfg: ProviderConfig) -> str:
    if cfg.id == "microsoft":
        return f"{MS_AUTHORITY}/{cfg.tenant or MS_DEFAULT_TENANT}/v2.0"
    if cfg.id == "google":
        return GOOGLE_ISSUER
    if cfg.id == "apple":
        return APPLE_ISSUER
    return (cfg.issuer or "").rstrip("/")


def clear_cache(cfg: ProviderConfig | None = None) -> None:
    _csp_cache.clear()
    if cfg is None:
        _discovery.clear()
        _jwks.clear()
    else:
        _discovery.pop(discovery_issuer(cfg), None)


def mock_issuer(provider: str) -> str:
    return f"urn:schulmanager:test-anbieter:{provider}"


def metadata(cfg: ProviderConfig) -> dict:
    """Endpunkte des Anbieters (Test-Anbieter: interne Seite; Apple: feste Adressen; sonst Discovery)."""
    if cfg.mock:
        return {"issuer": mock_issuer(cfg.id), "authorization_endpoint": f"{API}/auth/sso/{cfg.id}/mock",
                "token_endpoint": MOCK_TOKEN_ENDPOINT}
    if cfg.id == "apple":
        return {"issuer": APPLE_ISSUER, "authorization_endpoint": APPLE_AUTHORIZE, "token_endpoint": APPLE_TOKEN}
    return discovery(discovery_issuer(cfg))


def client_id(cfg: ProviderConfig) -> str:
    return MOCK_CLIENT_ID if cfg.mock else str(cfg.client_id or "")


def scopes(cfg: ProviderConfig) -> str:
    if cfg.id == "apple":
        return "name email"
    if cfg.id == "oidc" and not cfg.mock:
        return config.oidc_scopes
    return "openid email profile"


# =========================================================================== Content-Security-Policy je aktivem Anbieter
CSP_TTL = 30
_csp_cache: dict[str, tuple[float, dict[str, list[str]]]] = {}
#: Quellen je Anbieter und Richtlinie – Google: Doku „Content Security Policy“ der Identity Services; Apple: Skript
#: von appleid.cdn-apple.com, Schaltfläche/Popup von appleid.apple.com (nach Praxisberichten, nicht amtlich).
CSP_BY_PROVIDER: dict[str, dict[str, tuple[str, ...]]] = {
    "google": {"script-src": ("https://accounts.google.com/gsi/client",),
               "frame-src": ("https://accounts.google.com/gsi/",),
               "connect-src": ("https://accounts.google.com/gsi/",),
               "style-src": ("https://accounts.google.com/gsi/style",)},
    "apple": {"script-src": ("https://appleid.cdn-apple.com",),
              "frame-src": ("https://appleid.apple.com",),
              "connect-src": ("https://appleid.apple.com",),
              "style-src": ("https://appleid.cdn-apple.com",),
              "img-src": ("https://appleid.cdn-apple.com",)},
}


def csp_sources(db=None) -> dict[str, list[str]]:
    """Zusätzliche CSP-Quellen – nur für Anbieter, die eingerichtet UND eingeschaltet sind (nie Test-Anbieter)."""
    cached = _csp_cache.get("v")
    if cached and cached[0] > time.time():
        return cached[1]
    out: dict[str, list[str]] = {}
    own = None
    try:
        if db is None:
            from .db import SessionLocal

            own = db = SessionLocal()
        for pid, rules in CSP_BY_PROVIDER.items():
            if resolve(db, pid).enabled:
                for directive, sources in rules.items():
                    out.setdefault(directive, [])
                    out[directive] += [x for x in sources if x not in out[directive]]
    except Exception:  # noqa: BLE001 – Datenbank nicht erreichbar: keine Erweiterung (sicherer Standard)
        log.exception("CSP-Quellen der Anmeldedienste nicht ermittelbar")
        out = {}
    finally:
        if own is not None:
            own.close()
    _csp_cache["v"] = (time.time() + CSP_TTL, out)
    return out


def extend_csp(base: str, extra: dict[str, list[str]]) -> str:
    """Hängt Quellen an die Richtlinien einer CSP an (fehlt die Richtlinie: Werte von ``default-src`` + Quellen)."""
    if not extra:
        return base
    directives = [d.strip() for d in base.split(";") if d.strip()]
    names = {d.split()[0]: i for i, d in enumerate(directives)}
    for name, sources in extra.items():
        if name in names:
            directives[names[name]] += " " + " ".join(sources)
        else:
            base_value = directives[names["default-src"]].split(None, 1)[1] if "default-src" in names else "'self'"
            directives.append(f"{name} {base_value} {' '.join(sources)}")
    return "; ".join(directives)


# =========================================================================== Signierte Werte (Status, Test-Code)
def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _mac_key(purpose: str) -> bytes:
    return hmac.new(config.secret_key.encode(), f"schulmanager-sso:{purpose}".encode(), hashlib.sha256).digest()


def sign(payload: dict, purpose: str) -> str:
    """HMAC-signierter, kompakter Wert (zweckgebunden: ein Status ist kein Test-Code und umgekehrt)."""
    raw = b64(json.dumps({**payload, "typ": purpose}, separators=(",", ":")).encode())
    mac = hmac.new(_mac_key(purpose), raw.encode(), hashlib.sha256).digest()
    return f"{raw}.{b64(mac)}"


def unsign(value: str | None, purpose: str) -> dict | None:
    if not value or "." not in value or len(value) > 8192:
        return None
    raw, mac = value.rsplit(".", 1)
    expected = b64(hmac.new(_mac_key(purpose), raw.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(mac, expected):
        return None
    try:
        payload = json.loads(unb64(raw))
    except ValueError:
        return None
    if not isinstance(payload, dict) or payload.get("typ") != purpose:
        return None
    return payload if float(payload.get("exp", 0)) > time.time() else None


def pkce_challenge(verifier: str) -> str:
    return b64(hashlib.sha256(verifier.encode()).digest())


# =========================================================================== Ablauf
def new_flow(cfg: ProviderConfig, *, mode: str, next_path: str, user_id: int | None = None,
             session_id: int | None = None, silent: bool = False, login_hint: str | None = None,
             keep_sessions: list[str] | None = None) -> tuple[str, str]:
    """Startet eine Anmeldung bzw. Verknüpfung → (Adresse beim Anbieter, signierter Status-Cookie).

    ``silent``: stilles SSO (``prompt=none`` + ``login_hint``) – scheitert ohne Anbieter-Sitzung ohne Rückfrage.
    ``keep_sessions``: bisher angemeldete Sitzungen beim Kontowechsel (``?add=true``), siehe ``routes.auth``.
    """
    meta = metadata(cfg)
    state, nonce, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    hint = clean_email(login_hint) if silent else None
    url = authorization_url(cfg, meta, state=state, nonce=nonce, challenge=pkce_challenge(verifier), silent=silent,
                            login_hint=hint)
    payload = {"p": cfg.id, "s": state, "n": nonce, "v": verifier, "nx": next_path, "m": mode, "mock": cfg.mock,
               "exp": time.time() + STATE_TTL}
    if silent:
        payload["si"] = True
    if keep_sessions:
        payload["ks"] = keep_sessions[:8]
    if mode == "link":
        payload.update({"u": user_id, "sid": session_id})
    return url, sign(payload, "state")


def new_token_state(cfg: ProviderConfig, *, keep_sessions: list[str] | None = None) -> tuple[str, str]:
    """Nonce + Status-Cookie für ID-Tokens, die der Browser direkt liefert (Google One Tap, Apple JS)."""
    nonce = secrets.token_urlsafe(24)
    payload: dict[str, Any] = {"p": cfg.id, "s": secrets.token_urlsafe(8), "n": nonce, "m": "token", "mock": False,
                               "exp": time.time() + STATE_TTL}
    if keep_sessions:
        payload["ks"] = keep_sessions[:8]
    return nonce, sign(payload, "state")


def authorization_url(cfg: ProviderConfig, meta: dict, *, state: str, nonce: str, challenge: str,
                      silent: bool = False, login_hint: str | None = None) -> str:
    params = {"response_type": "code", "client_id": client_id(cfg), "redirect_uri": redirect_uri(cfg),
              "scope": scopes(cfg), "state": state, "nonce": nonce}
    if cfg.pkce:
        params.update({"code_challenge": challenge, "code_challenge_method": "S256"})
    if cfg.form_post:
        params["response_mode"] = "form_post"
    if silent and cfg.id != "apple" and not cfg.mock:
        params["prompt"] = "none"
        if login_hint:
            params["login_hint"] = login_hint
    elif cfg.id in ("microsoft", "google"):
        params["prompt"] = "select_account"      # gemeinsam genutzte Schulrechner: Konto immer auswählen
    if cfg.id == "google" and cfg.hosted_domain and not cfg.mock:
        params["hd"] = cfg.hosted_domain
    endpoint = meta["authorization_endpoint"]
    return f"{endpoint}{'&' if '?' in endpoint else '?'}{urllib.parse.urlencode(params)}"


def decode_id_token(token: str) -> dict:
    parts = str(token).split(".")
    if len(parts) != 3:
        raise ProviderError("ID-Token ist kein JWT")
    try:
        claims = json.loads(unb64(parts[1]))
    except ValueError:
        raise ProviderError("ID-Token nicht lesbar") from None
    if not isinstance(claims, dict):
        raise ProviderError("ID-Token nicht lesbar")
    return claims


_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def expected_issuer(cfg: ProviderConfig, meta: dict, claims: dict) -> str:
    issuer = str(meta.get("issuer") or discovery_issuer(cfg))
    if "{tenantid}" in issuer:
        tid = str(claims.get("tid") or "")
        if not _GUID.match(tid):
            raise ProviderError("tid fehlt oder ist ungültig")
        issuer = issuer.replace("{tenantid}", tid)
    return issuer


def validate_claims(cfg: ProviderConfig, meta: dict, claims: dict, nonce: str, *,
                    nonce_hashed_ok: bool = False) -> None:
    iss = str(claims.get("iss", "")).rstrip("/")
    allowed_iss = {expected_issuer(cfg, meta, claims).rstrip("/")}
    if cfg.id == "google":
        allowed_iss.add("accounts.google.com")      # Google nennt beide Schreibweisen als gültig
    if iss not in allowed_iss:
        raise ProviderError("Falscher Aussteller (iss)")
    cid = client_id(cfg)
    aud = claims.get("aud")
    audiences = aud if isinstance(aud, list) else [aud]
    if cid not in audiences:
        raise ProviderError("Falsche Zielgruppe (aud)")
    if len(audiences) > 1 and claims.get("azp") not in (None, cid):
        raise ProviderError("Falscher autorisierter Empfänger (azp)")
    try:
        exp = float(claims.get("exp", 0))
    except (TypeError, ValueError):
        exp = 0.0
    if exp < time.time() - 60:
        raise ProviderError("ID-Token abgelaufen")
    got = str(claims.get("nonce", ""))
    ok = bool(got) and hmac.compare_digest(got, nonce)
    if not ok and nonce_hashed_ok and got:
        ok = hmac.compare_digest(got, hashlib.sha256(nonce.encode()).hexdigest())
    if not ok:
        raise ProviderError("Nonce stimmt nicht")
    if not claims.get("sub"):
        raise ProviderError("sub fehlt")


# =========================================================================== ID-Token vom Browser (JWKS)
JWKS_TTL = 3600
JWKS_REFETCH_MIN = 30                       # unbekannte ``kid``: höchstens alle 30 s neu laden
GOOGLE_JWKS = "https://www.googleapis.com/oauth2/v3/certs"
APPLE_JWKS = "https://appleid.apple.com/auth/keys"
ID_TOKEN_MAX = 8192
_jwks: dict[str, tuple[float, float, dict]] = {}     # uri → (gültig bis, geladen um, Schlüsselsatz)


def jwks_uri(cfg: ProviderConfig, meta: dict) -> str:
    if cfg.id == "apple":
        return APPLE_JWKS
    return _check_endpoint(meta.get("jwks_uri") or (GOOGLE_JWKS if cfg.id == "google" else None), "jwks_uri")


def fetch_jwks(uri: str, *, force: bool = False) -> dict:
    now = time.time()
    cached = _jwks.get(uri)
    if cached and not force and cached[0] > now:
        return cached[2]
    if cached and force and now - cached[1] < JWKS_REFETCH_MIN:
        return cached[2]
    data = http_json(uri)
    if not isinstance(data, dict) or not isinstance(data.get("keys"), list):
        raise ProviderError("Schlüsselsatz (JWKS) ist ungültig")
    _jwks[uri] = (now + JWKS_TTL, now, data)
    return data


def _rsa_public_key(jwk: dict):
    from cryptography.hazmat.primitives.asymmetric import rsa

    try:
        n, e = int.from_bytes(unb64(jwk["n"]), "big"), int.from_bytes(unb64(jwk["e"]), "big")
        return rsa.RSAPublicNumbers(e, n).public_key()
    except (KeyError, ValueError, TypeError):
        raise ProviderError("Öffentlicher Schlüssel ist ungültig") from None


def verify_signed_jwt(token: str, uri: str) -> dict:
    """Signatur (RS256) über den Schlüsselsatz des Anbieters prüfen → Claims. ``alg: none``/HS* werden abgelehnt."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    if not isinstance(token, str) or len(token) > ID_TOKEN_MAX:
        raise ProviderError("ID-Token fehlt oder ist zu groß")
    parts = token.split(".")
    if len(parts) != 3:
        raise ProviderError("ID-Token ist kein JWT")
    try:
        header = json.loads(unb64(parts[0]))
        signature = unb64(parts[2])
    except ValueError:
        raise ProviderError("ID-Token nicht lesbar") from None
    if not isinstance(header, dict) or header.get("alg") != "RS256" or not header.get("kid"):
        raise ProviderError("Nicht unterstütztes Signaturverfahren")
    kid = str(header["kid"])

    def find(keys: dict) -> dict | None:
        for jwk in keys.get("keys", []):
            if isinstance(jwk, dict) and jwk.get("kid") == kid and jwk.get("kty") == "RSA" \
                    and jwk.get("alg") in (None, "RS256") and jwk.get("use") in (None, "sig"):
                return jwk
        return None

    jwk = find(fetch_jwks(uri)) or find(fetch_jwks(uri, force=True))
    if jwk is None:
        raise ProviderError("Signaturschlüssel unbekannt")
    try:
        _rsa_public_key(jwk).verify(signature, f"{parts[0]}.{parts[1]}".encode(), padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        raise ProviderError("Signatur des ID-Tokens ungültig") from None
    return decode_id_token(token)


def id_token_claims(cfg: ProviderConfig, token: str, nonce: str) -> dict:
    """ID-Token, das der Browser geliefert hat (One Tap / Apple JS): Signatur + alle Claims prüfen."""
    if cfg.mock or not cfg.enabled:
        raise ProviderError("Anbieter ist nicht eingerichtet")
    meta = metadata(cfg)
    claims = verify_signed_jwt(token, jwks_uri(cfg, meta))
    validate_claims(cfg, meta, claims, nonce, nonce_hashed_ok=cfg.id == "apple")
    return claims


def client_secret(cfg: ProviderConfig) -> str | None:
    if cfg.id == "apple":
        return apple_client_secret(cfg)
    return cfg.client_secret or None


def fetch_claims(cfg: ProviderConfig, meta: dict, code: str, saved: dict) -> dict:
    """Code → geprüfte Claims (Test-Anbieter: Test-Code lokal auflösen)."""
    if cfg.mock:
        claims = redeem_mock_code(cfg, code, saved["v"])
        validate_claims(cfg, meta, claims, saved["n"])
        return claims
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri(cfg),
            "client_id": client_id(cfg)}
    if cfg.pkce:
        data["code_verifier"] = saved["v"]
    secret = client_secret(cfg)
    if secret:
        data["client_secret"] = secret
    tokens = http_json(meta["token_endpoint"], data)
    if not isinstance(tokens, dict) or not tokens.get("id_token"):
        raise ProviderError("Token-Antwort ohne id_token")
    claims = decode_id_token(tokens["id_token"])
    validate_claims(cfg, meta, claims, saved["n"])
    if cfg.id == "oidc" and meta.get("userinfo_endpoint") and tokens.get("access_token") \
            and not claims.get(config.oidc_username_claim):
        info = http_json(meta["userinfo_endpoint"], headers={"Authorization": f"Bearer {tokens['access_token']}"})
        if isinstance(info, dict) and info.get("sub") == claims["sub"]:
            claims = {**info, **claims}
    return claims


# =========================================================================== Identität aus Claims
@dataclass
class Identity:
    provider: str
    subject: str
    email: str | None
    email_verified: bool
    name: str
    username: str | None
    claims: dict
    mock: bool = False


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]+$")


def clean_email(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    return text if _EMAIL.match(text) and len(text) <= 254 else None


def identity_from_claims(cfg: ProviderConfig, claims: dict) -> Identity:
    sub = str(claims["sub"])[:200]
    if cfg.mock:
        subject = sub
    elif cfg.id == "oidc":
        subject = f"{cfg.issuer}|{sub}"          # wie bisher users.oidc_sub
    else:
        subject = sub
    email = clean_email(claims.get("email"))
    verified = False
    if cfg.id == "microsoft":
        upn = clean_email(claims.get("preferred_username"))
        if upn and "#ext#" in upn:
            upn = None                           # Gastkonten: UPN ist keine echte Adresse
        if email and (_truthy(claims.get("xms_edov")) or email == upn):
            verified = True
        elif email is None and upn:
            email, verified = upn, True
        if email and not verified and (cfg.tenant or "").lower() not in MS_MULTI_TENANT:
            verified = True                      # fester Mandant: Adressen verwaltet die Schule selbst
    elif cfg.id in ("google", "apple"):
        verified = bool(email) and _truthy(claims.get("email_verified", False))
    else:  # oidc – IdP der Schule; ohne Angabe gilt die Adresse wie bisher als bestätigt
        verified = bool(email) and _truthy(claims.get("email_verified", True))
    name = str(claims.get("name") or " ".join(str(claims.get(k) or "") for k in ("given_name", "family_name"))
               or "").strip()
    username = claims.get(config.oidc_username_claim) or claims.get("preferred_username")
    return Identity(provider=cfg.id, subject=subject, email=email, email_verified=verified, name=name[:200],
                    username=str(username) if username else None, claims=claims, mock=cfg.mock)


def domain_problem(cfg: ProviderConfig, ident: Identity) -> str | None:
    """Fehlercode, wenn das Anbieter-Konto nicht zu den erlaubten Domains passt (sonst ``None``)."""
    if cfg.id == "google" and cfg.hosted_domain and not cfg.mock:
        if str(ident.claims.get("hd") or "").lower() != cfg.hosted_domain:
            return "domain_not_allowed"
    if cfg.allowed_domains:
        if not ident.email or not ident.email_verified:
            return "email_unverified"
        if ident.email.rsplit("@", 1)[1] not in cfg.allowed_domains:
            return "domain_not_allowed"
    return None


# =========================================================================== Apple: Client-Secret (ES256)
def load_apple_key(pem: str):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    try:
        key = serialization.load_pem_private_key(pem.encode(), password=None)
    except (ValueError, TypeError):
        raise ValueError("Der private Schlüssel ist keine gültige .p8-Datei (PEM, ohne Passwort).") from None
    if not isinstance(key, ec.EllipticCurvePrivateKey) or key.curve.name != "secp256r1":
        raise ValueError("Apple erwartet einen EC-Schlüssel (P-256) für „Sign in with Apple“.")
    return key


def apple_client_secret(cfg: ProviderConfig, *, now: float | None = None, lifetime: int = 600) -> str:
    """JWT (ES256) als Client-Secret: Header ``kid``, Claims iss=Team-ID, iat, exp (≤ 180 Tage),
    aud=``https://appleid.apple.com``, sub=Client-ID (Services-ID)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

    if not (cfg.private_key and cfg.team_id and cfg.key_id and cfg.client_id):
        raise ProviderError("Apple ist nicht vollständig eingerichtet")
    key = load_apple_key(cfg.private_key)
    iat = int(now if now is not None else time.time())
    header = {"alg": "ES256", "kid": cfg.key_id}
    claims = {"iss": cfg.team_id, "iat": iat, "exp": iat + max(60, min(int(lifetime), APPLE_SECRET_MAX)),
              "aud": APPLE_ISSUER, "sub": cfg.client_id}
    signing_input = ".".join(b64(json.dumps(part, separators=(",", ":")).encode()) for part in (header, claims))
    r, s = decode_dss_signature(key.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256())))
    return f"{signing_input}.{b64(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))}"


# =========================================================================== Test-Anbieter
def mock_subject(provider: str, email: str) -> str:
    return "mock:" + hashlib.sha256(f"{provider}|{email.strip().lower()}".encode()).hexdigest()[:40]


def issue_mock_code(cfg: ProviderConfig, *, email: str, name: str, nonce: str, challenge: str) -> str:
    if not cfg.mock:
        raise ProviderError("Test-Anbieter ist nicht aktiv")
    return sign({"p": cfg.id, "email": email, "name": name[:200], "n": nonce, "cc": challenge,
                 "jti": secrets.token_urlsafe(12), "exp": time.time() + MOCK_CODE_TTL}, "mock_code")


def redeem_mock_code(cfg: ProviderConfig, code: str, verifier: str) -> dict:
    """„Token-Austausch“ des Test-Anbieters: Code prüfen (Signatur, Anbieter, Ablauf, PKCE, einmalig) → Claims."""
    if not cfg.mock or not mock_enabled():
        raise ProviderError("Test-Anbieter ist nicht aktiv")
    data = unsign(code, "mock_code")
    if data is None or data.get("p") != cfg.id:
        raise ProviderError("Test-Code ungültig oder abgelaufen")
    if not hmac.compare_digest(str(data.get("cc", "")), pkce_challenge(verifier)):
        raise ProviderError("PKCE-Prüfung fehlgeschlagen")
    now = time.time()
    for jti, until in list(_used_mock_codes.items()):
        if until < now:
            _used_mock_codes.pop(jti, None)
    if data["jti"] in _used_mock_codes:
        raise ProviderError("Test-Code wurde bereits verwendet")
    _used_mock_codes[data["jti"]] = now + MOCK_CODE_TTL
    email = str(data["email"])
    claims: dict[str, Any] = {"iss": mock_issuer(cfg.id), "aud": MOCK_CLIENT_ID, "sub": mock_subject(cfg.id, email),
                              "exp": now + 300, "iat": now, "nonce": data.get("n"), "email": email,
                              "name": data.get("name") or email.split("@")[0]}
    if cfg.id == "microsoft":
        claims.update({"tid": MOCK_TENANT, "preferred_username": email})
    elif cfg.id == "apple":
        claims.update({"email_verified": "true", "is_private_email": "false"})
    elif cfg.id == "google":
        claims.update({"email_verified": True})
    else:
        claims.update({"email_verified": True, "preferred_username": email.split("@")[0]})
    return claims
