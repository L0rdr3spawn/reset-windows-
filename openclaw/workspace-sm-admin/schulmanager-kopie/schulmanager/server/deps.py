"""FastAPI-Abhängigkeiten für Authentifizierung und Rechte.

Verwendung in Routern::

    from schulmanager.server.deps import AuthUser, current_user, optional_user, require

    @router.get("/beispiel")
    def beispiel(user: AuthUser = Depends(require("timetable.edit"))): ...

Authentifizierung:
* Cookie ``sm_session`` (Sitzung) – zustandsändernde Methoden brauchen Header ``X-CSRF-Token``.
* ``Authorization: Bearer <token>`` (API-Token) – kein CSRF nötig.
* Konten mit ``must_change_password`` erhalten überall außer ``/auth/*`` den Fehler
  ``403 {"detail": "password_change_required"}``.
* Rollen aus ``SM_REQUIRE_2FA_ROLES`` ohne aktive 2FA erhalten (Sitzungs-Login) überall außer ``/auth/*``
  ``403 {"detail": "totp_setup_required"}``.
* Fehlen laut Anmelde-Richtlinie (§11.5) Pflicht-Verknüpfungen (``AuthUser.login_setup``), gibt es überall außer
  ``/auth/*`` und ``/me/identities*`` ``403 {"detail": "link_required"}``. Ist das Passwort als Anmeldeweg nicht
  erlaubt, entfällt der Passwortwechsel-Zwang.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import config
from .db import get_db, utcnow
from .db_models import ApiToken, User, UserSession
from .permissions import ROLE_LABELS, effective_rights, own_class_ids, permissions_for, scope_for
from .security import constant_equals, hash_token

log = logging.getLogger("schulmanager.auth")

SESSION_COOKIE = "sm_session"
CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
# Pfade (ohne /api/v1), die auch mit Passwortwechsel-Zwang erreichbar sind
PASSWORD_CHANGE_ALLOWED = ("/auth/",)
# … und mit fehlenden Pflicht-Verknüpfungen (§11.5; ``/auth/sso/*`` liegt unter ``/auth/``)
LINK_SETUP_ALLOWED = ("/auth/", "/me/identities")
_SLIDING_UPDATE_SECONDS = 60


@dataclass
class AuthUser:
    """Angemeldeter Benutzer (unveränderliche Sicht für Handler)."""
    id: int
    username: str
    display_name: str
    role: str
    permissions: set[str] = field(default_factory=set)
    teacher_id: str | None = None
    student_id: str | None = None
    student_ids: list[str] = field(default_factory=list)   # Eltern: Kinder; Schüler: [eigene]
    site: str | None = None
    must_change_password: bool = False
    totp_enabled: bool = False
    email: str | None = None
    adult: bool = False
    auth_method: str = "session"          # session|token|ical|system
    session_id: int | None = None
    csrf_token: str | None = None
    # Anmelde-Richtlinie (§11.5): {"missing_links": [...], "setup_only": bool} oder None
    login_setup: dict[str, Any] | None = None
    # Wirksame Einschränkungen (Standard + Schul-Einstellungen); ``None`` = Standardwerte der Rolle
    scopes: dict[str, str] | None = None
    # Abteilungsleitung: Zweige ``[{id, name, sites, grades, class_ids}]``
    branches: list[dict[str, Any]] = field(default_factory=list)
    # API-Zugang mit Umfang (``api_scopes``): Token-ID und gespeicherter Umfang; ``None`` = Sitzung/persönliches Token
    api_token_id: int | None = None
    api_scope: dict[str, Any] | None = None
    # Zwei-Faktor-Vorgabe der Schule für die Rolle: ``required`` | ``recommended`` | ``""`` (security_settings)
    twofa_policy: str = ""

    def has(self, permission: str) -> bool:
        return permission in self.permissions

    def scope(self, permission: str) -> str | None:
        """Einschränkung eines Rechts (z. B. ``own_classes``) oder ``None`` = uneingeschränkt."""
        if self.scopes is not None:
            return self.scopes.get(permission)
        return scope_for(self.role, permission)

    def class_ids(self, school) -> set[str]:
        """Eigene Klassen (Lehrkraft: unterrichtete, Schüler/Eltern: eigene bzw. der Kinder)."""
        return own_class_ids(school, self)

    def public(self) -> dict[str, Any]:
        """Darstellung für ``/auth/me`` und Login-Antwort."""
        return {
            "id": self.id, "username": self.username, "display_name": self.display_name, "role": self.role,
            "role_label": ROLE_LABELS.get(self.role, self.role), "permissions": sorted(self.permissions), "teacher_id": self.teacher_id,
            "student_id": self.student_id, "student_ids": list(self.student_ids), "site": self.site,
            "must_change_password": self.must_change_password, "totp_enabled": self.totp_enabled,
            "totp_setup_required": self.totp_setup_required, "totp_recommended": self.totp_recommended,
            "email": self.email,
            "login_setup": self.login_setup,
        }

    @property
    def totp_setup_required(self) -> bool:
        """2FA ist für die Rolle Pflicht, aber noch nicht eingerichtet (nur Sitzungs-Logins)."""
        return (self.twofa_policy == "required" and not self.totp_enabled and self.auth_method == "session")

    @property
    def totp_recommended(self) -> bool:
        """Die Schule empfiehlt 2FA für diese Rolle, das Konto hat sie noch nicht (Hinweis auf der Startseite)."""
        return self.twofa_policy == "recommended" and not self.totp_enabled and self.auth_method == "session"


SYSTEM_USER = AuthUser(id=0, username="system", display_name="System", role="admin",
                       permissions=permissions_for("admin"), auth_method="system")


def build_auth_user(db: Session, user: User, **extra: Any) -> AuthUser:
    """ORM-``User`` → :class:`AuthUser` (inkl. Rechte laut Schul-Einstellungen, Kinder-IDs, Zweige).

    Schulbegleitung: ``student_id`` = erstes begleitetes Kind, damit Kursräume und Pläne wie beim Kind greifen;
    ``student_ids`` = alle begleiteten Kinder."""
    from . import rights
    student_ids: list[str] = []
    student_id = user.student_id
    if user.role in ("eltern", "schulbegleitung"):
        student_ids = rights.user_children(db, user.id)
        if user.role == "schulbegleitung":
            student_id = student_ids[0] if student_ids else None
    elif user.role == "schueler" and user.student_id:
        student_ids = [user.student_id]
    from .parent_access import effective_adult
    adult = effective_adult(db, user)   # Schüler: Geburtsdatum geht vor dem Konto-Merkmal (Minderjährige melden sich nie selbst krank)
    perms, scopes = effective_rights(user.role, adult, rights.load_overrides(db, user.role))
    branches = rights.user_branches(db, user.id) if user.role == "abteilungsleitung" else []
    from . import security_settings
    try:
        twofa = security_settings.twofa_policy(db, user.role)
    except Exception:  # noqa: BLE001 - fehlende Tabelle o. Ä. darf die Anmeldung nicht lahmlegen
        log.exception("Sicherheits-Einstellungen nicht lesbar")
        twofa = "required" if user.role in config.require_2fa_roles else ""
    au = AuthUser(
        id=user.id, username=user.username, display_name=user.display_name or user.username, role=user.role,
        permissions=perms, teacher_id=user.teacher_id, student_id=student_id, student_ids=student_ids,
        site=user.site, must_change_password=bool(user.must_change_password), totp_enabled=bool(user.totp_enabled),
        email=user.email, adult=adult, scopes=scopes, branches=branches, twofa_policy=twofa, **extra)
    _apply_login_policy(db, au)
    return au


def _apply_login_policy(db: Session, au: AuthUser) -> None:
    """Anmelde-Richtlinie (§11.5): ohne erlaubtes Passwort kein Passwortwechsel-Zwang; fehlende
    Pflicht-Verknüpfungen → ``login_setup`` (Sperre ``link_required`` in :func:`current_user`)."""
    try:
        from . import identities, login_policy

        policy = login_policy.effective_policy(db, au)
        password_allowed = "password" in policy.methods
        if not password_allowed:
            au.must_change_password = False
        if policy.required_links:
            linked = set(identities.linked_providers(db, au.id) or ())
            missing = [p for p in identities.PROVIDERS if p in policy.required_links and p not in linked]
            if missing:
                au.login_setup = {"missing_links": missing, "setup_only": not password_allowed}
    except Exception:  # noqa: BLE001 – Richtlinie darf die Anmeldung nie komplett lahmlegen
        log.exception("Anmelde-Richtlinie für Konto %s nicht auswertbar", au.id)


def user_from_ical_token(db: Session, token: str) -> AuthUser | None:
    """Löst das geheime Token eines iCal-Feeds (``users.ical_token``) auf; ``None`` wenn ungültig/inaktiv."""
    if not token or len(token) < 16:
        return None
    from .security import hash_token

    user = db.scalar(select(User).where(User.ical_token == hash_token(token)))
    if user is None or not user.active:
        return None
    return build_auth_user(db, user, auth_method="ical")


def client_ip(request: Request) -> str | None:
    """Client-IP; hinter einem Reverse Proxy (``SM_TRUST_PROXY=1``) aus ``X-Forwarded-For``."""
    if config.trust_proxy:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            parts = [p.strip() for p in fwd.split(",") if p.strip()]
            if parts:
                return parts[-min(config.proxy_count, len(parts))][:64]
        real = request.headers.get("x-real-ip")
        if real:
            return real.strip()[:64]
    return request.client.host if request.client else None


def request_is_https(request: Request) -> bool:
    """Kam die Anfrage des Browsers per HTTPS? Hinter einem Proxy (``SM_TRUST_PROXY=1``) zählt ``X-Forwarded-Proto``."""
    if config.trust_proxy:
        proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
        if proto:
            return proto == "https"
    return request.url.scheme == "https"


def cookie_secure_for(request: Request | None) -> bool:
    """``Secure``-Attribut für Cookies: immer bei ``SM_COOKIE_SECURE=1``, sonst automatisch bei HTTPS-Anfragen
    (HTTP im Heimnetz funktioniert weiter, HTTPS-Zugriff bekommt trotzdem ``Secure``)."""
    return config.cookie_secure or (request is not None and request_is_https(request))


def same_origin(request: Request, origin: str) -> bool:
    """Passt der ``Origin`` einer Anfrage zu diesem Server – auch hinter Proxy mit anderem Port/Host-Header?
    Erlaubt: ``Host``, ``X-Forwarded-Host`` (nur mit ``SM_TRUST_PROXY=1``) und die konfigurierte ``SM_BASE_URL``."""
    from urllib.parse import urlsplit

    try:
        parts = urlsplit(origin)
    except ValueError:
        return False
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return False
    allowed = {request.headers.get("host", "").lower(), urlsplit(config.base_url).netloc.lower()}
    if config.trust_proxy:
        fwd = request.headers.get("x-forwarded-host", "").split(",")[0].strip().lower()
        if fwd:
            allowed.add(fwd)
            if "x-forwarded-port" in request.headers and ":" not in fwd:
                allowed.add(f"{fwd}:{request.headers['x-forwarded-port'].split(',')[0].strip()}")
        # Proxy lässt den Port im Host-Header weg (nginx ``$host``): Hostname gleich + Schema aus X-Forwarded-Proto
        host = request.headers.get("host", "").lower()
        if host and parts.hostname == host.split(":")[0] and parts.scheme == ("https" if request_is_https(request) else "http"):
            return True
    return parts.netloc.lower() in allowed - {""}


def _api_path(request: Request) -> str:
    path = request.url.path
    return path[len("/api/v1"):] if path.startswith("/api/v1") else path


def authenticate(request: Request, db: Session, *, enforce_csrf: bool = True) -> AuthUser | None:
    """Ermittelt den Benutzer aus Bearer-Token oder Sitzungs-Cookie (``None`` = anonym).

    Wirft 403 ``csrf_failed`` bei Cookie-Auth ohne gültigen CSRF-Header (unsichere Methoden).
    Verlängert die Sitzung gleitend (höchstens bis zur absoluten Höchstdauer).
    """
    cached = getattr(request.state, "auth_user", None)
    if cached is not None:
        return cached
    now = utcnow()
    auth = request.headers.get("authorization", "")
    if auth[:7].lower() == "bearer ":
        token = auth[7:].strip()
        if not token:
            return None
        row = db.scalar(select(ApiToken).where(ApiToken.token_hash == hash_token(token)))
        if row is None or (row.expires_at is not None and row.expires_at < now) or row.revoked_at is not None:
            raise HTTPException(401, "invalid_token")
        user = db.get(User, row.user_id)
        if user is None or not user.active:
            raise HTTPException(401, "invalid_token")
        if row.scope is not None:      # Zugang mit Umfang: nur /open/…, IP, Ratenlimit (api_scopes)
            from . import api_scopes
            api_scopes.check_request(request, db, row)
        if row.last_used is None or (now - row.last_used).total_seconds() > _SLIDING_UPDATE_SECONDS:
            row.last_used = now
            db.commit()
        au = build_auth_user(db, user, auth_method="token", api_token_id=row.id if row.scope is not None else None,
                             api_scope=row.scope)
        _guard_read_only(request, au)
        _guard_demo(request, au, db)
        _guard_license(request)
        request.state.auth_user = au
        return au

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    sess = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if sess is None or sess.expires_at < now:
        return None
    user = db.get(User, sess.user_id)
    if user is None or not user.active:
        return None
    if enforce_csrf and request.method in UNSAFE_METHODS:
        if not constant_equals(request.headers.get(CSRF_HEADER), sess.csrf_token):
            raise HTTPException(403, "csrf_failed")
    if (now - sess.last_seen).total_seconds() > _SLIDING_UPDATE_SECONDS:
        hard_limit = sess.created_at + timedelta(days=config.session_max_days)
        sess.last_seen = now
        from . import security_settings
        idle = security_settings.idle_minutes(db, user.role)
        sess.expires_at = min(now + timedelta(minutes=idle), hard_limit)
        db.commit()
    au = build_auth_user(db, user, auth_method="session", session_id=sess.id, csrf_token=sess.csrf_token)
    _guard_read_only(request, au)
    _guard_demo(request, au, db)
    _guard_license(request)
    request.state.auth_user = au
    return au


READ_ONLY_ALLOWED = ("/auth/logout", "/auth/accounts")


DEMO_OWN_ACCOUNT = ("/auth/password", "/auth/2fa/")
DEMO_NOT_POSSIBLE = "In der öffentlichen Demo nicht möglich (die Demo-Konten bleiben für alle Besucher gleich)."


def _guard_demo(request: Request, au: AuthUser, db: Session) -> None:
    """Öffentliche Demo (``SM_DEMO_PUBLIC``): schreibende Anfragen nur laut Allowlist (``demo_guard.ALLOW``, neue Routen
    sind standardmäßig gesperrt), Demo-Konten bleiben für alle gleich; neue Konten, Klassen, Zugangsbriefe verschwinden
    beim nächsten Zurücksetzen."""
    if not config.demo_public or request.method not in UNSAFE_METHODS:
        return
    from . import demo_guard
    from .demo_loader import is_demo_account
    path = _api_path(request)
    demo_guard.check(request.method, path)
    if path.startswith(DEMO_OWN_ACCOUNT) and is_demo_account(au.username):
        raise HTTPException(403, DEMO_NOT_POSSIBLE)
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "users" and parts[1].isdigit() and au.username != config.admin_user:
        target = db.get(User, int(parts[1]))
        if target is not None and is_demo_account(target.username):
            raise HTTPException(403, DEMO_NOT_POSSIBLE)


LICENSE_ALLOWED = ("/auth/", "/license")


def _guard_license(request: Request) -> None:
    """Lizenz in der Kulanzzeit (``licensing.is_read_only()``): Lesen bleibt möglich, Änderungen nicht – außer
    Anmelden/Abmelden und dem Einspielen einer neuen Lizenz. Gesperrt (``is_locked()``): gar nichts."""
    if not config.license_enforce:
        return
    if _api_path(request).startswith(LICENSE_ALLOWED):
        return
    from . import licensing
    if licensing.is_locked():      # Absicherung; die Sperre selbst setzt ``license_lock.LicenseLockMiddleware`` durch
        raise HTTPException(403, "license_locked")
    if request.method not in UNSAFE_METHODS:
        return
    if licensing.is_read_only():
        raise HTTPException(403, f"Nur Lesen: {licensing.lock_message()} "
                                 "Bitte die Schulleitung bzw. Administration informieren.")


def _guard_read_only(request: Request, au: AuthUser) -> None:
    """Zuschauer-Konten (``permissions.READ_ONLY_ROLES``) dürfen nur lesen: jede ändernde Anfrage → 403."""
    from .permissions import READ_ONLY_ROLES
    if au.role in READ_ONLY_ROLES and request.method in UNSAFE_METHODS \
            and not _api_path(request).startswith(READ_ONLY_ALLOWED):
        raise HTTPException(403, "Ansichtskonto: Änderungen sind mit diesem Zugang nicht möglich.")


def optional_user(request: Request, db: Session = Depends(get_db)) -> AuthUser | None:
    """Dependency: angemeldeter Benutzer oder ``None``."""
    return authenticate(request, db)


def current_user(request: Request, db: Session = Depends(get_db)) -> AuthUser:
    """Dependency: angemeldeter Benutzer, sonst 401 ``not_authenticated``."""
    user = authenticate(request, db)
    if user is None:
        raise HTTPException(401, "not_authenticated")
    if user.must_change_password and not _api_path(request).startswith(PASSWORD_CHANGE_ALLOWED):
        raise HTTPException(403, "password_change_required")
    if user.totp_setup_required and not _api_path(request).startswith(PASSWORD_CHANGE_ALLOWED):
        raise HTTPException(403, "totp_setup_required")
    if user.login_setup and user.login_setup.get("missing_links") \
            and not _api_path(request).startswith(LINK_SETUP_ALLOWED):
        raise HTTPException(403, "link_required")
    return user


def require(*permissions: str, any_of: bool = False) -> Callable[..., AuthUser]:
    """Dependency-Fabrik: verlangt alle (bzw. mit ``any_of=True`` mindestens eines der) Rechte, sonst 403."""
    perms = tuple(permissions)

    def dependency(user: AuthUser = Depends(current_user)) -> AuthUser:
        ok = any(p in user.permissions for p in perms) if any_of else all(p in user.permissions for p in perms)
        if perms and not ok:
            raise HTTPException(403, "Keine Berechtigung für diese Aktion")
        return user

    dependency.__name__ = "require_" + "_".join(p.replace(".", "_") for p in perms)
    return dependency
