"""Anmeldung, Sitzung, Passwort, Zwei-Faktor-Authentifizierung."""
from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..accounts import create_session, revoke_sessions
from ..audit import audit
from ..config import config
from ..db import get_db, utcnow
from ..db_models import User, UserSession
from ..deps import (
    SESSION_COOKIE,
    AuthUser,
    authenticate,
    build_auth_user,
    client_ip,
    cookie_secure_for,
    current_user,
    same_origin,
)
from .. import login_throttle
from ..metrics import metrics
from ..security import (
    MIN_LENGTH,
    MIN_LENGTH_DEFAULT,
    get_totp_secret,
    hash_password,
    hash_token,
    needs_rehash,
    new_totp_secret,
    otpauth_url,
    password_problems,
    set_totp_secret,
    verify_password,
    verify_totp,
)

router = APIRouter(prefix="/auth", tags=["Anmeldung"])


class LoginBody(BaseModel):
    username: str = Field(max_length=200)
    password: str = Field(max_length=1024)
    totp: str | None = Field(default=None, max_length=12)


class PasswordBody(BaseModel):
    old_password: str = Field(default="", max_length=1024)
    new_password: str = Field(max_length=1024)


class CodeBody(BaseModel):
    code: str = Field(max_length=12)


class PasswordOnlyBody(BaseModel):
    password: str = Field(max_length=1024)


# --------------------------------------------------------------------------- Drosselung (S-04)
def _lock_status(db: Session, username: str, ip: str | None) -> int:
    """Sekunden bis zum nächsten erlaubten Versuch (0 = frei) – progressive Verzögerung, siehe ``login_throttle``."""
    return login_throttle.status(db, username, ip).wait


def _record(db: Session, username: str, ip: str | None, success: bool) -> None:
    login_throttle.record(db, username, ip, success)


def _fail(db: Session, username: str, ip: str | None, detail: str, status: int = 401) -> HTTPException:
    _record(db, username, ip, False)
    metrics.login("failure")
    return HTTPException(status, detail)


def user_payload(au: AuthUser) -> dict:
    """``AuthUser.public()`` + Namen/Klassen der verknüpften Schüler (``students``)."""
    from ..store import get_store

    data = au.public()
    data["demo"] = config.demo_public
    from .. import licensing
    lic = licensing.status()
    from .license import SHORT_KEYS
    data["license"] = {k: lic.get(k) for k in SHORT_KEYS}
    if au.student_ids:
        index = get_store().school.index("students")
        data["students"] = [{"id": sid, "name": index[sid].name if sid in index else sid,
                             "class_id": index[sid].class_id if sid in index else None} for sid in au.student_ids]
    else:
        data["students"] = []
    return data


def set_session_cookie(response: Response, token: str, request: Request | None = None) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=config.session_max_days * 86400, httponly=True,
                        samesite="lax", secure=cookie_secure_for(request), path="/")


def login_user(db: Session, user: User, request: Request, response: Response, method: str = "password") -> dict:
    """Erzeugt Sitzung + Cookie für einen bereits geprüften Benutzer (auch für SSO)."""
    ip = client_ip(request)
    user.last_login = utcnow()
    token, sess = create_session(db, user, request, ip)
    audit(db, user, "auth.login", f"user:{user.id}", {"method": method}, ip=ip)
    db.commit()
    set_session_cookie(response, token, request)
    metrics.login("success")
    au = build_auth_user(db, user, auth_method="session", session_id=sess.id, csrf_token=sess.csrf_token)
    return {"user": user_payload(au), "csrf_token": sess.csrf_token}


# --------------------------------------------------------------------------- Endpunkte
# --------------------------------------------------------------------------- mehrere Konten
#: weitere angemeldete Konten dieses Browsers (Sitzungstoken, ``~``-getrennt; httponly wie ``sm_session``)
OTHERS_COOKIE = "sm_sessions"
MAX_ACCOUNTS = 5


def _others(request: Request) -> list[str]:
    raw = request.cookies.get(OTHERS_COOKIE) or ""
    return [t for t in raw.split("~") if t][: MAX_ACCOUNTS]


def _set_others(response: Response, tokens: list[str], request: Request | None = None) -> None:
    secure = cookie_secure_for(request)
    tokens = list(dict.fromkeys(t for t in tokens if t))[: MAX_ACCOUNTS - 1]
    if tokens:
        response.set_cookie(OTHERS_COOKIE, "~".join(tokens), max_age=config.session_max_days * 86400, httponly=True,
                            samesite="lax", secure=secure, path="/")
    else:
        response.delete_cookie(OTHERS_COOKIE, path="/", samesite="lax", secure=secure, httponly=True)


def _valid_session(db: Session, token: str) -> tuple[UserSession, User] | None:
    sess = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if sess is None or sess.expires_at < utcnow():
        return None
    user = db.get(User, sess.user_id)
    if user is None or not user.active:
        return None
    return sess, user


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response, add: bool = Query(False),
          db: Session = Depends(get_db)) -> dict:
    """Anmeldung mit Benutzername/Passwort (+ TOTP bei aktivierter 2FA). Setzt Cookie ``sm_session``.
    Zweistufig: Hat das Konto 2FA und fehlt ``totp``, antwortet der Server (nach richtigem Passwort) mit
    ``{"totp_required": true}`` ohne Sitzung; der Aufruf wird dann mit Code wiederholt.
    ``add=true``: weiteres Konto anmelden – das bisherige bleibt angemeldet (Wechsel über ``/auth/accounts``)."""
    previous = request.cookies.get(SESSION_COOKIE) if add else None
    result = _login(body, request, response, db)
    if add and "user" in result:
        keep_sessions(db, response, ([previous] if previous else []) + _others(request), result["user"]["id"], request)
    return result


def current_sessions(request: Request) -> list[str]:
    """Bisher angemeldete Sitzungen dieses Browsers (aktive zuerst) – für den Kontowechsel über SSO (``add=true``)."""
    first = request.cookies.get(SESSION_COOKIE)
    return ([first] if first else []) + _others(request)


def keep_sessions(db: Session, response: Response, tokens: list[str], new_uid: int,
                  request: Request | None = None) -> None:
    """Nach ``add=true``: gültige bisherige Sitzungen (außer der des neuen Kontos) als weitere Konten behalten."""
    keep = []
    for tok in tokens:
        found = _valid_session(db, tok)
        if found and found[1].id != new_uid:
            keep.append(tok)
    _set_others(response, keep, request)


def _login(body: LoginBody, request: Request, response: Response, db: Session) -> dict:
    ip = client_ip(request)
    username = body.username.strip().lower()[:80]
    wait = _lock_status(db, username, ip)
    if wait > 0:
        metrics.login("locked")
        raise HTTPException(429, "too_many_attempts", headers={"Retry-After": str(wait)})
    user = db.scalar(select(User).where(func.lower(User.username) == username))
    if not verify_password(body.password, user.password_hash if user else None) or user is None:
        raise _fail(db, username, ip, "invalid_credentials")
    if not user.active:
        raise _fail(db, username, ip, "account_disabled", 403)
    if user.totp_enabled:
        # Zweistufig (S-16 neu bewertet, docs/SICHERHEIT.md): Erst nach richtigem Passwort fragt der Server nach dem
        # Code. Das verrät „Passwort stimmt“ nur dem, der es ohnehin kennt; Raten des Passworts bleibt gedrosselt
        # (jedes falsche Passwort zählt). Schritt 1 wird weder als Fehlversuch noch als Erfolg gezählt – ein Erfolg
        # würde die Fehlversuche beim Raten des Codes zurücksetzen. Ein falscher oder wiederverwendeter Code zählt
        # wie ein falsches Passwort.
        if not body.totp:
            metrics.login("totp_required")
            return {"totp_required": True}
        if not verify_totp(get_totp_secret(user), body.totp, replay_key=str(user.id)):
            raise _fail(db, username, ip, "invalid_credentials")
    if user.must_change_password and _initial_expired(db, user):
        audit(db, user, "auth.login_denied", f"user:{user.id}", {"method": "password", "reason": "initial_expired"},
              ip=ip)
        raise _fail(db, username, ip, "initial_password_expired", 403)
    # Anmelde-Richtlinie (§11.5) – erst nach vollständig geprüften Zugangsdaten (keine Konto-Erkennung).
    # Ersteinrichtung (Startpasswort + fehlende Pflicht-Verknüpfung) → Sitzung nur zum Verbinden.
    from ..login_policy import login_methods_hint, password_login

    decision, policy = password_login(db, user)
    if decision == "denied":
        audit(db, user, "auth.login_denied", f"user:{user.id}", {"method": "password",
                                                                  "reason": "method_not_allowed"}, ip=ip)
        _record(db, username, ip, False)
        metrics.login("failure")
        raise HTTPException(403, "method_not_allowed",
                            headers={"X-Login-Methods": ",".join(login_methods_hint(policy))})
    _record(db, username, ip, True)
    if needs_rehash(user.password_hash) and not user.must_change_password:
        user.password_hash = hash_password(body.password)
    return login_user(db, user, request, response, method="password_setup" if decision == "setup" else "password")


def _initial_expired(db: Session, user: User) -> bool:
    """Ist das Passwort noch das Startpasswort und dessen Frist abgelaufen? (Erst nach geprüftem Passwort aufrufen.)"""
    from ..feature_models.letters import AccountInitialPassword

    row = db.get(AccountInitialPassword, user.id)
    if row is None:
        return False
    if row.password_hash != user.password_hash:          # inzwischen ein anderes Passwort → Marke ist überholt
        db.delete(row)
        db.commit()
        return False
    return row.expires_at <= utcnow()


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Beendet die aktuelle Sitzung (CSRF-Header nötig, falls angemeldet). Es wird **kein** anderes Konto aktiv: die
    übrigen in diesem Browser angemeldeten Konten bleiben nur in ``sm_sessions`` und werden auf der Seite
    „Abgemeldet“ zur Auswahl angeboten (``accounts`` = Anzahl der noch gültigen)."""
    user = authenticate(request, db)
    token = request.cookies.get(SESSION_COOKIE)
    # Abmelden heißt: kein stilles SSO / keine Auto-Auswahl beim nächsten Besuch der Anmeldeseite
    response.delete_cookie("sm_sso_hint", path="/", samesite="lax", secure=cookie_secure_for(request))
    response.delete_cookie("sm_sso_who", path="/", samesite="lax", secure=cookie_secure_for(request), httponly=True)
    if user is not None and token:
        sess = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
        if sess is not None:
            db.delete(sess)
        audit(db, user, "auth.logout", f"user:{user.id}", ip=client_ip(request))
        db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="lax", secure=cookie_secure_for(request), httponly=True)
    # weitere Konten bleiben angemeldet, aber inaktiv; ungültige/doppelte Tokens fallen heraus
    keep = _valid_others(db, request, exclude_user_id=user.id if user is not None else None)
    _set_others(response, [tok for tok, _ in keep], request)
    return {"ok": True, "accounts": len(keep)}


def _valid_others(db: Session, request: Request, exclude_user_id: int | None = None) -> list[tuple[str, User]]:
    """Gültige weitere Sitzungen dieses Browsers (Token, Benutzer), ohne Doppelte und ohne ``exclude_user_id``."""
    out: list[tuple[str, User]] = []
    seen: set[int] = set() if exclude_user_id is None else {exclude_user_id}
    for tok in _others(request):
        found = _valid_session(db, tok)
        if found and found[1].id not in seen:
            seen.add(found[1].id)
            out.append((tok, found[1]))
    return out


#: Kopfzeile, die Browser-Seitenaufrufe von fremden Seiten aus nicht setzen können (erzwingt CORS-Vorabprüfung)
CLIENT_HEADER = "X-Requested-With"
CLIENT_HEADER_VALUE = "schulmanager"


def _optional_session_user(request: Request, db: Session) -> AuthUser | None:
    """Kontolisten-Endpunkte funktionieren auch **ohne** aktive Sitzung (Seite „Abgemeldet“): dann gibt es kein
    Sitzungs-CSRF-Token, also verlangt der Aufruf eine eigene Kopfzeile + passenden ``Origin`` (SameSite=Lax hält
    das Cookie ohnehin von fremden POSTs fern). Mit aktiver Sitzung gilt das übliche CSRF-Token."""
    user = authenticate(request, db)
    if user is not None:
        return user
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get(CLIENT_HEADER) != CLIENT_HEADER_VALUE:
            raise HTTPException(403, "csrf_failed")
        origin = request.headers.get("origin")
        if origin:
            if not same_origin(request, origin):
                raise HTTPException(403, "csrf_failed")
    return None


class SwitchBody(BaseModel):
    user_id: int


@router.get("/accounts")
def accounts(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Alle in diesem Browser angemeldeten Konten (aktives zuerst). Ohne aktive Sitzung (nach dem Abmelden) nur die
    noch gültigen weiteren Konten – ohne Daten, die über Name/Rolle hinausgehen."""
    user = _optional_session_user(request, db)
    out: list[dict] = []
    if user is not None:
        out.append({"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role,
                    "active": True})
    keep = _valid_others(db, request, exclude_user_id=user.id if user is not None else None)
    for _tok, u in keep:
        out.append({"id": u.id, "username": u.username, "display_name": u.display_name, "role": u.role,
                    "active": False})
    if len(keep) != len(_others(request)):
        _set_others(response, [tok for tok, _ in keep], request)     # ungültige Tokens aus dem Cookie entfernen
    return {"accounts": out, "max": MAX_ACCOUNTS, "signed_in": user is not None}


@router.post("/accounts/switch")
def switch_account(body: SwitchBody, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Zu einem anderen angemeldeten Konto wechseln (ohne Passwort – die Sitzung besteht schon). Geht auch ohne aktive
    Sitzung (nach dem Abmelden), aber nur mit gültigem Token aus ``sm_sessions``."""
    user = _optional_session_user(request, db)
    current = request.cookies.get(SESSION_COOKIE) or "" if user is not None else ""
    others = _others(request)
    for tok in others:
        found = _valid_session(db, tok)
        if found and found[1].id == body.user_id:
            sess, target = found
            set_session_cookie(response, tok, request)
            _set_others(response, [current] + [t for t in others if t != tok], request)
            audit(db, target, "auth.switch_account", f"user:{target.id}",
                  {"from": user.username if user else None}, ip=client_ip(request))
            db.commit()
            au = build_auth_user(db, target, auth_method="session", session_id=sess.id, csrf_token=sess.csrf_token)
            return {"user": user_payload(au), "csrf_token": sess.csrf_token}
    raise HTTPException(404, "Dieses Konto ist in diesem Browser nicht angemeldet.")


@router.post("/accounts/{user_id}/logout")
def logout_other(user_id: int, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Ein weiteres (nicht aktives) Konto abmelden – auch ohne aktive Sitzung (Seite „Abgemeldet“)."""
    user = _optional_session_user(request, db)
    keep = []
    for tok in _others(request):
        found = _valid_session(db, tok)
        if found and found[1].id == user_id:
            db.delete(found[0])
            audit(db, found[1], "auth.logout", f"user:{user_id}", {"by": user.username if user else "abgemeldet"},
                  ip=client_ip(request))
        elif found:
            keep.append(tok)
    db.commit()
    _set_others(response, keep, request)
    return {"ok": True, "accounts": len(keep)}


@router.get("/me")
def me(user: AuthUser = Depends(current_user)) -> dict:
    """Angemeldeter Benutzer inkl. Rechten und CSRF-Token."""
    return {"user": user_payload(user), "csrf_token": user.csrf_token}


@router.get("/config")
def auth_config() -> dict:
    """Öffentliche Anmelde-Konfiguration (für die Login-Seite)."""
    return {"app_name": config.app_name, "env": config.env,
            "oidc": {"enabled": config.oidc_enabled, "label": config.oidc_label,
                     "login_url": "/api/v1/auth/oidc/login" if config.oidc_enabled else None},
            "password_min_length": {"default": MIN_LENGTH_DEFAULT, **MIN_LENGTH}}


def _session_only(user: AuthUser) -> None:
    if user.auth_method != "session":
        raise HTTPException(403, "Nur mit angemeldeter Sitzung möglich")


def _check_lock(db: Session, username: str, ip: str | None) -> None:
    """Passwortprüfungen in der Sitzung (Passwortwechsel, 2FA abschalten) unterliegen derselben Sperre."""
    wait = _lock_status(db, username, ip)
    if wait > 0:
        raise HTTPException(429, "too_many_attempts", headers={"Retry-After": str(wait)})


@router.post("/password")
def change_password(body: PasswordBody, request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    """Eigenes Passwort ändern. Beendet alle anderen Sitzungen des Kontos."""
    _session_only(user)
    row = db.get(User, user.id)
    assert row is not None
    ip = client_ip(request)
    _check_lock(db, row.username, ip)
    if row.password_hash and not verify_password(body.old_password, row.password_hash):
        _record(db, row.username, ip, False)
        raise HTTPException(400, "Das bisherige Passwort ist falsch.")
    problems = password_problems(body.new_password, row.role, row.username)
    if not problems and verify_password(body.new_password, row.password_hash):
        problems.append("Das neue Passwort muss sich vom bisherigen unterscheiden.")
    if problems:
        raise HTTPException(422, " ".join(problems))
    row.password_hash = hash_password(body.new_password)
    row.must_change_password = False
    from ..letters import clear_initial
    clear_initial(db, row.id)                      # das Startpasswort ist ersetzt (S-06)
    revoked = revoke_sessions(db, row.id, except_session_id=user.session_id)
    audit(db, user, "auth.password_change", f"user:{row.id}", {"revoked_sessions": revoked}, ip=ip)
    db.commit()
    return {"ok": True}


@router.post("/2fa/setup")
def totp_setup(neu: bool = False, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """TOTP-Geheimnis für die Einrichtung (noch nicht aktiv – erst mit ``/2fa/enable`` bestätigen). Eine begonnene,
    unbestätigte Einrichtung behält ihr Geheimnis (derselbe QR-Code, die App bleibt gültig); ``neu=true`` erzeugt
    ein neues."""
    _session_only(user)
    row = db.get(User, user.id)
    assert row is not None
    if row.totp_enabled:
        raise HTTPException(409, "Zwei-Faktor-Anmeldung ist bereits aktiv.")
    if neu or not get_totp_secret(row):
        set_totp_secret(row, new_totp_secret())
        db.commit()
    secret = get_totp_secret(row) or ""
    return {"secret": secret, "otpauth_url": otpauth_url(secret, row.username)}


@router.post("/2fa/enable")
def totp_enable(body: CodeBody, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    _session_only(user)
    row = db.get(User, user.id)
    assert row is not None
    if row.totp_enabled:
        raise HTTPException(409, "Zwei-Faktor-Anmeldung ist bereits aktiv.")
    if not get_totp_secret(row):
        raise HTTPException(409, "Bitte zuerst /auth/2fa/setup aufrufen.")
    if not verify_totp(get_totp_secret(row), body.code, replay_key=str(row.id)):
        raise HTTPException(400, "invalid_totp")
    row.totp_enabled = True
    audit(db, user, "auth.2fa_enable", f"user:{row.id}", ip=client_ip(request))
    db.commit()
    return {"ok": True, "totp_enabled": True}


@router.post("/2fa/disable")
def totp_disable(body: PasswordOnlyBody, request: Request, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    _session_only(user)
    row = db.get(User, user.id)
    assert row is not None
    _check_lock(db, row.username, client_ip(request))
    if not verify_password(body.password, row.password_hash):
        _record(db, row.username, client_ip(request), False)
        raise HTTPException(400, "Das Passwort ist falsch.")
    row.totp_enabled = False
    set_totp_secret(row, None)
    audit(db, user, "auth.2fa_disable", f"user:{row.id}", ip=client_ip(request))
    db.commit()
    return {"ok": True, "totp_enabled": False}
