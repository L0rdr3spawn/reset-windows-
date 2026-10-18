"""Verbundene Anbieter-Konten (Microsoft, Apple, Google, Schulkonto) – docs/ARCHITECTURE.md §11.4.

VERTRAG (Besitzer: Agent Anbieter). Stabile Signaturen für alle Agenten:

* :data:`PROVIDERS` / :data:`PROVIDER_LABELS` – unterstützte Anbieter.
* :func:`linked_providers` – Anbieter, mit denen ein Konto verbunden ist (nur bestätigte Verknüpfungen mit ``subject``).
* :func:`available_providers` – Anbieter, die gerade nutzbar sind: eingerichtet + eingeschaltet, oder – mit
  ``SM_SSO_DEV_MOCK`` in der Entwicklung – nicht eingerichtete als Test-Anbieter (``mock: true``).

Weitere Helfer (für ``routes/features_sso.py``): :func:`identity_rows`, :func:`public_identity`,
:func:`find_login_user` (Anbieter-Konto → Schulmanager-Konto), :func:`provider_label`.
Tabelle: ``feature_models/identities.py`` (``user_identities``, ``sso_providers``).
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("schulmanager.identities")

PROVIDERS: tuple[str, ...] = ("microsoft", "apple", "google", "oidc")
PROVIDER_LABELS: dict[str, str] = {"microsoft": "Microsoft", "apple": "Apple", "google": "Google",
                                   "oidc": "Schulkonto"}


def linked_providers(db, user_id: int) -> set[str]:
    """Anbieter mit bestätigter Verknüpfung (``subject`` gesetzt) – eine Abfrage, wird bei jeder Anfrage genutzt."""
    from sqlalchemy import select

    from .feature_models.identities import UserIdentity

    rows = db.scalars(select(UserIdentity.provider).where(UserIdentity.user_id == int(user_id),
                                                          UserIdentity.subject.is_not(None)))
    return set(rows)


#: Art der Anmeldung auf der Login-Seite: ``redirect`` (Weiterleitung), ``microsoft`` (offizieller Knopf + Weiterleitung,
#: stilles SSO), ``gis`` (Google Identity Services), ``apple_js`` (Sign in with Apple JS im Popup)
def _flow(cfg) -> str:
    if cfg.mock:
        return "redirect"
    return {"microsoft": "microsoft", "google": "gis", "apple": "apple_js"}.get(cfg.id, "redirect")


def available_providers(db=None) -> list[dict]:
    """``[{id, label, mock, flow, auto, client_id?, redirect_uri?}]`` der nutzbaren Anbieter (Reihenfolge wie
    :data:`PROVIDERS`). ``client_id`` (öffentlich) nur für ``gis``/``apple_js``; ``auto`` = automatische Anmeldung."""
    from . import sso_providers

    if db is None:
        from .db import SessionLocal

        with SessionLocal() as own:
            return available_providers(own)
    out: list[dict[str, Any]] = []
    for pid in PROVIDERS:
        cfg = sso_providers.resolve(db, pid)
        if not cfg.usable:
            continue
        flow = _flow(cfg)
        item: dict[str, Any] = {"id": pid, "label": cfg.label, "mock": cfg.mock and not cfg.enabled, "flow": flow,
                                "auto": bool(cfg.enabled and cfg.auto_signin)}
        if flow in ("gis", "apple_js"):
            item["client_id"] = cfg.client_id
        if flow == "apple_js":
            item["redirect_uri"] = sso_providers.redirect_uri(cfg)
        out.append(item)
    return out


def provider_label(provider: str, db=None) -> str:
    from . import sso_providers

    try:
        return sso_providers.resolve(db, provider).label
    except KeyError:
        return provider


def identity_rows(db, user_id: int) -> list:
    from sqlalchemy import select

    from .feature_models.identities import UserIdentity

    rows = list(db.scalars(select(UserIdentity).where(UserIdentity.user_id == int(user_id))))
    order = {p: i for i, p in enumerate(PROVIDERS)}
    return sorted(rows, key=lambda r: order.get(r.provider, 99))


def public_identity(row, label: str | None = None) -> dict[str, Any]:
    """Darstellung für Profil und Benutzerverwaltung – ohne ``subject``."""
    from .db import iso

    return {"provider": row.provider, "label": label or PROVIDER_LABELS.get(row.provider, row.provider),
            "email": row.email, "email_verified": bool(row.email_verified), "linked": row.subject is not None,
            "pending": row.subject is None, "mock": bool(row.subject and row.subject.startswith("mock:")),
            "managed": row.created_by is not None and row.created_by != row.user_id,
            "created_at": iso(row.created_at), "last_login_at": iso(row.last_login_at)}


def find_login_user(db, cfg, ident) -> tuple[Any, Any, str]:
    """Anbieter-Konto → ``(User | None, UserIdentity | None, wie)`` (ohne Commit).

    Reihenfolge: 1. bestehende Verknüpfung (provider, subject); 2. vom Admin vorgemerkte Verknüpfung mit gleicher,
    vom Anbieter **bestätigter** E-Mail (eindeutig); 3. nur mit ``login_policy.effective_policy(...).sso_create``:
    Konto mit gleicher ``users.email`` (eindeutig, noch ohne Verknüpfung dieses Anbieters); 4. nur Schulkonto
    (``oidc``): bisherige Zuordnung über Benutzername/E-Mail und ``SM_OIDC_AUTO_CREATE``.
    """
    from sqlalchemy import func, select

    from .db import utcnow
    from .db_models import User
    from .feature_models.identities import UserIdentity

    row = db.scalar(select(UserIdentity).where(UserIdentity.provider == cfg.id, UserIdentity.subject == ident.subject))
    if row is not None:
        return db.get(User, row.user_id), row, "linked"

    def _attach(user, how: str, existing=None):
        target = existing or UserIdentity(user_id=user.id, provider=cfg.id, created_at=utcnow())
        target.subject = ident.subject
        target.email = ident.email
        target.email_verified = bool(ident.email_verified)
        if existing is None:
            db.add(target)
        db.flush()
        return user, target, how

    email = ident.email if ident.email_verified else None
    if email:
        reserved = list(db.scalars(select(UserIdentity).where(UserIdentity.provider == cfg.id,
                                                              UserIdentity.subject.is_(None),
                                                              func.lower(UserIdentity.email) == email)))
        if len(reserved) == 1:
            user = db.get(User, reserved[0].user_id)
            if user is not None:
                return _attach(user, "reserved", reserved[0])
        candidates = list(db.scalars(select(User).where(func.lower(User.email) == email).limit(2)))
        if len(candidates) == 1 and not _has_row(db, candidates[0].id, cfg.id):
            from . import login_policy

            if login_policy.effective_policy(db, candidates[0]).sso_create:
                return _attach(candidates[0], "email")
    if cfg.id == "oidc":
        user = _legacy_oidc_user(db, cfg, ident)
        if user is not None:
            return _attach(user, "legacy")
        if _config().oidc_auto_create:
            return _attach(_create_oidc_user(db, ident), "created")
    return None, None, ""


def _config():
    from .config import config

    return config


def _has_row(db, user_id: int, provider: str) -> bool:
    from sqlalchemy import select

    from .feature_models.identities import UserIdentity

    return db.scalar(select(UserIdentity.id).where(UserIdentity.user_id == user_id,
                                                   UserIdentity.provider == provider)) is not None


def _legacy_oidc_user(db, cfg, ident):
    """Schulkonto: bisherige Erst-Zuordnung über Benutzername bzw. bestätigte E-Mail (IdP der Schule)."""
    from sqlalchemy import func, select

    from .accounts import normalize_username
    from .db_models import User

    stmts = []
    if ident.username:
        name = str(ident.username)
        stmts.append(select(User).where(User.username == normalize_username(name.split("@")[0])))
        stmts.append(select(User).where(func.lower(User.username) == name.lower()))
    if ident.email and ident.email_verified:
        stmts.append(select(User).where(func.lower(User.email) == ident.email))
    for stmt in stmts:
        for user in db.scalars(stmt.limit(2)):
            if not _has_row(db, user.id, cfg.id):
                return user
    return None


def _create_oidc_user(db, ident):
    """Neues Konto über das Schulkonto (``SM_OIDC_AUTO_CREATE``), wie bisher ohne Passwort, nie Admin."""
    from .accounts import create_user, unique_username
    from .permissions import ROLES

    config = _config()
    role = config.oidc_default_role if config.oidc_default_role in ROLES else "lehrer"
    if role == "admin":
        role = "lehrer"
    base = str(ident.username or ident.email or "sso").split("@")[0]
    user, _ = create_user(db, username=unique_username(db, base), role=role, display_name=ident.name or base,
                          password_hash="", must_change_password=False, email=ident.email or None)
    user.password_hash = None
    return user
