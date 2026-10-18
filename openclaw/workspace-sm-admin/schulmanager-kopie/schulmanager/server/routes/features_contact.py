"""Kontakt & Wiederherstellung (Erweiterung 4, §11.2): E-Mail/Handy bestätigen, „Passwort vergessen“,
Admin-Pflege der Kontaktdaten und Test-Postausgang.

Endpunkte (Präfix ``/api/v1``)
------------------------------
Eigenes Konto (angemeldet, Schreiben nur mit Sitzung + CSRF; aktuelles Passwort, falls das Konto eines hat):

* ``GET  /me/contact`` – E-Mail (+ bestätigt), Nummer maskiert (+ bestätigt), offene Bestätigungen, verfügbare
  Kanäle, ``reset_channels`` laut Anmelde-Richtlinie.
* ``POST /me/contact/email {email, password}`` / ``POST /me/contact/phone {phone, password}`` – Code an die **neue**
  Adresse/Nummer senden (E-Mail zusätzlich mit Bestätigungslink ``/profil?kontakt=<token>``). Gültig wird sie erst
  nach ``POST /me/contact/verify {kind, code}`` bzw. ``POST /me/contact/confirm-link {token}``.
* ``POST /me/contact/{email|phone}/remove {password}``.

„Passwort vergessen“ (ohne Anmeldung, kein CSRF nötig – es wird keine Sitzung benutzt):

* ``GET  /auth/capabilities`` (= ``/auth/password-reset/options``) – öffentlich, ohne Geheimnisse: ``email``/``sms``
  (Versand wirklich möglich), ``channels`` (dasselbe als Objekt), ``self_reset {rolle: bool}`` (darf die Rolle laut
  Anmelde-Richtlinie „Passwort vergessen“ selbst nutzen?). Die Oberfläche zeigt E-Mail-/SMS-Wege nur, wenn sie gehen.
* ``POST /auth/password-reset/request {identifier, channel}`` – Benutzername, E-Mail oder Handynummer; Antwort
  **immer gleich** und mit Mindestlaufzeit (:data:`MIN_RESPONSE_SECONDS`). Zugestellt wird nur an **bestätigte**
  Kontakte und nur, wenn die Richtlinie den Kanal (``reset_channels``) und ``password`` (``methods``) erlaubt.
  Rate-Limit je Kennung (5/h) und IP (20/h) – gilt genauso für unbekannte Kennungen; je Konto höchstens 5 Codes/h
  über alle Kennungen (darüber still verworfen, gleiche Antwort).
* ``POST /auth/password-reset/verify {token}`` (Link aus der E-Mail) oder ``{identifier, code}`` → kurzlebiges
  ``reset_token`` (nur als Hash gespeichert). Versuche werden vor dem Vergleich atomar gezählt und Codes/Links atomar
  verbraucht – parallele Anfragen umgehen weder die 5 Versuche je Code noch die Einmaligkeit.
* ``POST /auth/password-reset/confirm {reset_token, new_password}`` – Passwortregeln, ``must_change_password=False``,
  alle Sitzungen beendet, Audit; 2FA bleibt aktiv.

Verwaltung (``users.manage`` + ``_check_manage`` – das Sekretariat also nur für Schüler/innen und Eltern):

* ``GET/PUT /users/{id}/contact`` – setzen, als bestätigt markieren, Nummer entfernen.
* ``POST /users/{id}/send-reset {channel}`` – Link/Code zum Zurücksetzen an den bestätigten Kontakt senden.

Test-Postausgang (nur ``SM_DEV_OUTBOX``, sonst 404): ``GET /dev-outbox``, ``GET /dev-outbox/{id}/attachments/{n}``.
"""
from __future__ import annotations

import asyncio
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from .. import auth_messages, crypto, sms
from ..accounts import revoke_sessions
from ..audit import audit
from ..config import config
from ..db import get_db, iso, session_scope, utcnow
from ..db_models import LoginAttempt, User
from ..deps import AuthUser, client_ip, current_user, require
from ..feature_models.contact import AuthCode, UserContact
from ..security import hash_password, hash_token, min_length, new_token, password_problems, verify_password

log = logging.getLogger("schulmanager.contact")

router = APIRouter(tags=["Kontakt & Wiederherstellung"])

CODE_DIGITS = 6
MAX_ATTEMPTS = 5                  # Fehlversuche je Code
RESET_PER_IDENT_HOUR = 5          # „Passwort vergessen“-Anfragen je Kennung
RESET_PER_USER_HOUR = 5           # Codes zum Zurücksetzen je Konto (alle Kennungen zusammen; darüber still verworfen)
RESET_PER_IP_HOUR = 20            # … je IP
CODES_PER_USER_HOUR = 5           # Bestätigungscodes je Konto und Art
CODES_PER_IP_HOUR = 20
FAILS_PER_IP_HOUR = 30            # falsche Codes/Links je IP
ADMIN_SENDS_PER_USER_HOUR = 10    # „Link zum Zurücksetzen senden“ je Zielkonto
MAX_ACCOUNTS_PER_IDENT = 5        # E-Mail-Adressen dürfen mehreren Konten gehören (z. B. Eltern je Kind)
MIN_RESPONSE_SECONDS = 0.35       # gleiche Laufzeit für bekannte/unbekannte Kennungen (Tests setzen 0)
RL_WINDOW = timedelta(hours=1)

GENERIC_RESET_REPLY = "Falls ein Konto dazu passt, ist ein Code unterwegs."
TOO_MANY = ("Zu viele Anfragen. Bitte versuchen Sie es später erneut (spätestens in einer Stunde) oder wenden Sie "
            "sich an das Sekretariat.")
BAD_CODE = "Der Code ist falsch oder abgelaufen."
BAD_LINK = "Der Link ist ungültig oder abgelaufen. Bitte fordern Sie einen neuen an."
SAFE_ATTACHMENT_TYPES = {"application/pdf", "application/zip", "image/png", "image/jpeg", "text/plain", "text/csv",
                         "text/calendar"}


# =========================================================================== Modelle der Anfragen
class EmailStart(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(default="", max_length=1024)


class PhoneStart(BaseModel):
    phone: str = Field(max_length=40)
    password: str = Field(default="", max_length=1024)


class VerifyBody(BaseModel):
    kind: Literal["email", "phone"]
    code: str = Field(max_length=20)


class TokenBody(BaseModel):
    token: str = Field(max_length=200)


class PasswordBody(BaseModel):
    password: str = Field(default="", max_length=1024)


class AdminContactBody(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    email_verified: bool | None = None
    phone: str | None = Field(default=None, max_length=40)
    phone_verified: bool | None = None


class SendResetBody(BaseModel):
    channel: Literal["email", "sms"] = "email"


class ResetRequestBody(BaseModel):
    identifier: str = Field(min_length=1, max_length=254)
    channel: Literal["email", "sms", "auto"] = "auto"


class ResetVerifyBody(BaseModel):
    token: str | None = Field(default=None, max_length=200)
    identifier: str | None = Field(default=None, max_length=254)
    code: str | None = Field(default=None, max_length=20)


class ResetConfirmBody(BaseModel):
    reset_token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(max_length=1024)


# =========================================================================== Hilfen
def _minutes() -> int:
    return config.auth_code_minutes


def _new_code() -> str:
    return f"{secrets.randbelow(10 ** CODE_DIGITS):0{CODE_DIGITS}d}"


def _code_hash(purpose: str, user_id: int, code: str) -> str:
    return hash_token(f"authcode:{purpose}:{user_id}:{code}")


def _clean_code(code: str | None) -> str:
    return "".join(ch for ch in str(code or "") if ch.isdigit())


def _normalize_ident(identifier: str) -> str:
    raw = (identifier or "").strip()
    if "@" not in raw and sms.looks_like_phone(raw):
        phone = sms.normalize_phone(raw)
        if phone:
            return phone
    return raw.lower()


def _ident_hash(ident: str) -> str:
    return hash_token(f"reset-ident:{ident}")


def _site_name() -> str:
    try:
        from ..store import get_store

        name = get_store().school.settings.school_name
    except Exception:  # noqa: BLE001 - Planungsdokument noch nicht geladen
        name = ""
    return name if name and name != "Meine Schule" else config.app_name


def _session_only(user: AuthUser) -> None:
    if user.auth_method != "session":
        raise HTTPException(403, "Nur mit angemeldeter Sitzung möglich")


def _get_user(db: Session, user_id: int) -> User:
    row = db.get(User, user_id)
    if row is None:
        raise HTTPException(404, "Benutzer nicht gefunden")
    return row


def _contact(db: Session, user_id: int, *, create: bool = False) -> UserContact | None:
    row = db.get(UserContact, user_id)
    if row is None and create:
        row = UserContact(user_id=user_id, updated_at=utcnow())
        db.add(row)
    return row


def _phone_of(contact: UserContact | None) -> str | None:
    if contact is None or not contact.phone_enc:
        return None
    try:
        return crypto.decrypt_text(contact.phone_enc, f"user_contacts.phone:{contact.user_id}")
    except Exception:  # noqa: BLE001 - Schlüssel fehlt: wie „keine Nummer“
        log.warning("Handynummer von Konto %s nicht lesbar", contact.user_id)
        return None


def _email_verified(user: User, contact: UserContact | None) -> bool:
    email = (user.email or "").strip().lower()
    return bool(email and contact is not None and contact.email_verified_value == email)


def _sendable_email(user: User) -> bool:
    """Adresse lässt sich zustellen (``users.email`` wird anderswo ohne Formatprüfung gesetzt)."""
    return auth_messages.valid_email((user.email or "").strip())


def _phone_verified(contact: UserContact | None) -> bool:
    return bool(contact is not None and contact.phone_enc and contact.phone_verified_at)


def _set_phone(contact: UserContact, e164: str | None, *, verified: bool) -> None:
    now = utcnow()
    if e164 is None:
        contact.phone_enc = contact.phone_hash = contact.phone_verified_at = None
    else:
        contact.phone_enc = crypto.encrypt_text(e164, f"user_contacts.phone:{contact.user_id}")
        contact.phone_hash = sms.phone_hash(e164)
        contact.phone_verified_at = now if verified else None
    contact.updated_at = now


def _set_email_verified(user: User, contact: UserContact, verified: bool) -> None:
    now = utcnow()
    if verified and user.email:
        contact.email_verified_value = user.email.strip().lower()
        contact.email_verified_at = now
    else:
        contact.email_verified_value = contact.email_verified_at = None
    contact.updated_at = now


def _policy(db: Session, user: User) -> Any | None:
    """Wirksame Anmelde-Richtlinie (lazy, §11.5) – ``None``, wenn sie nicht ausgewertet werden kann."""
    try:
        from .. import login_policy

        return login_policy.effective_policy(db, user)
    except Exception:  # noqa: BLE001 - lieber kein Zurücksetzen als ein unbeabsichtigt erlaubtes
        log.exception("Anmelde-Richtlinie für Konto %s nicht auswertbar", getattr(user, "id", "?"))
        return None


def _password_login(policy: Any | None) -> bool:
    return policy is not None and "password" in set(getattr(policy, "methods", ()) or ())


def _reset_channels(policy: Any | None) -> list[str]:
    if not _password_login(policy):
        return []
    return sorted(c for c in (getattr(policy, "reset_channels", ()) or ()) if c in ("email", "sms"))


def _count(db: Session, *conditions: Any) -> int:
    return int(db.scalar(select(func.count(AuthCode.id)).where(*conditions)) or 0)


def _active_code(db: Session, user_id: int, purpose: str) -> AuthCode | None:
    now = utcnow()
    return db.scalar(select(AuthCode).where(AuthCode.user_id == user_id, AuthCode.purpose == purpose,
                                            AuthCode.used_at.is_(None), AuthCode.expires_at > now,
                                            AuthCode.attempts < MAX_ATTEMPTS)
                     .order_by(AuthCode.id.desc()).limit(1))


def _take_attempt(db: Session, row_id: int) -> int | None:
    """Einen Versuch für den Code **atomar** verbuchen, bevor er geprüft wird – parallele Anfragen können die Grenze
    :data:`MAX_ATTEMPTS` so nicht umgehen. → neue Anzahl der Versuche oder ``None`` (Code nicht mehr gültig).
    Commit macht der Aufrufer (vor dem Vergleich bzw. der Antwort)."""
    result = db.execute(update(AuthCode).where(AuthCode.id == row_id, AuthCode.used_at.is_(None),
                                               AuthCode.expires_at > utcnow(), AuthCode.attempts < MAX_ATTEMPTS)
                        .values(attempts=AuthCode.attempts + 1).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        return None
    return int(db.scalar(select(AuthCode.attempts).where(AuthCode.id == row_id)) or 0)


def _claim(db: Session, row_id: int) -> bool:
    """Code/Token **atomar** als verwendet markieren – nur eine von mehreren gleichzeitigen Anfragen gewinnt."""
    result = db.execute(update(AuthCode).where(AuthCode.id == row_id, AuthCode.used_at.is_(None))
                        .values(used_at=utcnow()).execution_options(synchronize_session=False))
    return result.rowcount == 1


def _target_of(row: AuthCode) -> str | None:
    if not row.target_enc:
        return None
    return crypto.decrypt_text(row.target_enc, f"auth_codes.target:{row.id}")


def _issue(db: Session, user_id: int, purpose: str, channel: str, ip: str | None, *, target: str | None = None,
           with_token: bool = False, ident_hash: str | None = None) -> tuple[AuthCode, str, str | None]:
    """Neuer Einmal-Code (ältere offene Codes desselben Zwecks werden entwertet). → (Zeile, Code, Link-Token)."""
    now = utcnow()
    db.execute(update(AuthCode).where(AuthCode.user_id == user_id, AuthCode.purpose == purpose,
                                      AuthCode.used_at.is_(None)).values(used_at=now))
    code = _new_code()
    token = new_token(32) if with_token else None
    row = AuthCode(user_id=user_id, purpose=purpose, channel=channel, code_hash=_code_hash(purpose, user_id, code),
                   token_hash=hash_token(token) if token else None, ident_hash=ident_hash,
                   expires_at=now + timedelta(minutes=_minutes()), attempts=0, ip=ip, created_at=now)
    db.add(row)
    db.flush()
    if target is not None:
        row.target_enc = crypto.encrypt_text(target, f"auth_codes.target:{row.id}")
    return row, code, token


def _limit_codes(db: Session, user_id: int, purpose: str, ip: str | None) -> None:
    since = utcnow() - RL_WINDOW
    if _count(db, AuthCode.user_id == user_id, AuthCode.purpose == purpose,
              AuthCode.created_at > since) >= CODES_PER_USER_HOUR:
        raise HTTPException(429, TOO_MANY, headers={"Retry-After": "3600"})
    if ip and _count(db, AuthCode.ip == ip, AuthCode.purpose.in_(("verify_email", "verify_phone")),
                     AuthCode.created_at > since) >= CODES_PER_IP_HOUR:
        raise HTTPException(429, TOO_MANY, headers={"Retry-After": "3600"})


def _check_password(db: Session, row: User, password: str, ip: str | None) -> None:
    """Aktuelles Passwort verlangen (falls gesetzt) – mit derselben Sperre wie bei der Anmeldung."""
    if not row.password_hash:
        return
    from .auth import _check_lock, _record

    _check_lock(db, row.username, ip)
    if not verify_password(password or "", row.password_hash):
        _record(db, row.username, ip, False)
        raise HTTPException(400, "Das Passwort ist falsch.")


# =========================================================================== Nachrichten
def _greeting(user: User) -> str:
    return f"Guten Tag {user.display_name}," if user.display_name else "Guten Tag,"


def _send_verify_email(db: Session, user: User, address: str, code: str, token: str | None) -> None:
    lines = [_greeting(user), "",
             f"bitte bestätigen Sie diese E-Mail-Adresse für Ihr Konto „{user.username}“ ({_site_name()}).", "",
             f"Bestätigungscode: {code}", ""]
    if token:
        lines += ["Oder öffnen Sie diesen Link (Anmeldung erforderlich):", f"{config.base_url}/profil?kontakt={token}",
                  ""]
    lines += [f"Code und Link sind {_minutes()} Minuten gültig. Wenn Sie das nicht veranlasst haben, können Sie "
              "diese Nachricht ignorieren.", "", "Diese Nachricht wurde automatisch erzeugt."]
    auth_messages.queue_email(db, address, f"E-Mail-Adresse bestätigen – {config.app_name}", "\n".join(lines),
                              purpose="verify_email")


def _send_verify_sms(db: Session, phone: str, code: str) -> None:
    auth_messages.queue_sms(db, phone, f"{config.app_name}: Ihr Bestätigungscode lautet {code} "
                                       f"({_minutes()} Min. gültig). Bitte nicht weitergeben.", purpose="verify_phone")


def _send_reset(db: Session, user: User, channel: str, ip: str | None, *,
                ident_hash: str | None = None) -> tuple[AuthCode, str]:
    """Code (+ Link bei E-Mail) zum Zurücksetzen erzeugen und verschicken. → (Code-Zeile, maskiertes Ziel)."""
    row, code, token = _issue(db, user.id, "reset", channel, ip, with_token=channel == "email", ident_hash=ident_hash)
    if channel == "email":
        address = (user.email or "").strip()
        text = "\n".join([
            _greeting(user), "",
            f"für Ihr Konto „{user.username}“ ({_site_name()}) wurde das Zurücksetzen des Passworts angefordert.", "",
            "Neues Passwort festlegen:", f"{config.base_url}/passwort-zuruecksetzen?token={token}", "",
            f"Oder geben Sie auf der Seite „Passwort vergessen?“ diesen Code ein: {code}", "",
            f"Link und Code sind {_minutes()} Minuten gültig und nur einmal verwendbar. Wenn Sie das nicht angefordert "
            "haben, ignorieren Sie diese Nachricht – Ihr Passwort bleibt unverändert.", "",
            "Diese Nachricht wurde automatisch erzeugt."])
        auth_messages.queue_email(db, address, f"Passwort zurücksetzen – {config.app_name}", text,
                                  purpose="password_reset")
        return row, auth_messages.mask_email(address)
    phone = _phone_of(_contact(db, user.id)) or ""
    auth_messages.queue_sms(db, phone, f"{config.app_name}: Code zum Zurücksetzen Ihres Passworts: {code} "
                                       f"({_minutes()} Min. gültig). Eingeben unter {config.base_url}"
                                       "/passwort-vergessen – nicht weitergeben.", purpose="password_reset")
    return row, sms.mask_phone(phone)


def _notify_old_email(db: Session, user: User, old_address: str, what: str) -> None:
    """Hinweis an die bisher bestätigte Adresse, wenn sich Kontaktdaten ändern (bestmöglich)."""
    if not old_address or not auth_messages.email_available():
        return
    text = "\n".join([_greeting(user), "", f"für Ihr Konto „{user.username}“ ({_site_name()}) wurde {what}.", "",
                      "Wenn Sie das nicht waren, ändern Sie bitte sofort Ihr Passwort und wenden Sie sich an das "
                      "Sekretariat.", "", "Diese Nachricht wurde automatisch erzeugt."])
    try:
        auth_messages.queue_email(db, old_address, f"Kontaktdaten geändert – {config.app_name}", text,
                                  purpose="contact_notice")
    except ValueError:
        pass


# =========================================================================== Darstellung
def _pending(db: Session, user_id: int) -> dict[str, Any]:
    out: dict[str, Any] = {"email": None, "phone": None}
    for kind, purpose in (("email", "verify_email"), ("phone", "verify_phone")):
        row = _active_code(db, user_id, purpose)
        if row is None:
            continue
        try:
            target = _target_of(row)
        except Exception:  # noqa: BLE001
            target = None
        if target:
            out[kind] = {"target": target if kind == "email" else sms.mask_phone(target),
                         "expires_at": iso(row.expires_at)}
    return out


def _channels() -> dict[str, bool]:
    return {"email": auth_messages.email_available(), "sms": auth_messages.sms_available()}


def _self_reset_by_role(db: Session) -> dict[str, bool]:
    """Je Rolle: darf man „Passwort vergessen“ selbst nutzen? (Rollen-Richtlinie: Passwort erlaubt + mind. ein Kanal)."""
    from .. import login_policy
    from ..permissions import ROLES

    out: dict[str, bool] = {}
    for role in ROLES:
        try:
            out[role] = bool(_reset_channels(login_policy.role_policy(db, role)))
        except Exception:  # noqa: BLE001 - lieber „nein“ als ein unbeabsichtigt erlaubtes Zurücksetzen
            log.exception("Richtlinie der Rolle %s nicht auswertbar", role)
            out[role] = False
    return out


def _capabilities(db: Session) -> dict[str, Any]:
    channels = _channels()
    return {"email": channels["email"], "sms": channels["sms"], "channels": channels,
            "self_reset": _self_reset_by_role(db), "code_minutes": _minutes(),
            "dev_outbox": auth_messages.dev_outbox_enabled()}


def _my_contact(db: Session, user: User) -> dict[str, Any]:
    contact = _contact(db, user.id)
    phone = _phone_of(contact)
    email_ok, phone_ok = _email_verified(user, contact), _phone_verified(contact)
    policy = _policy(db, user)
    return {
        "email": user.email or None, "email_verified": email_ok,
        "email_verified_at": iso(contact.email_verified_at) if email_ok and contact else None,
        "phone": sms.mask_phone(phone) if phone else None, "phone_verified": phone_ok,
        "phone_verified_at": iso(contact.phone_verified_at) if phone_ok and contact else None,
        "has_password": bool(user.password_hash), "password_login": _password_login(policy),
        "reset_channels": _reset_channels(policy), "channels": _channels(), "pending": _pending(db, user.id),
        "code_minutes": _minutes(), "dev_outbox": auth_messages.dev_outbox_enabled(),
    }


def _admin_contact(db: Session, user: User) -> dict[str, Any]:
    contact = _contact(db, user.id)
    phone = _phone_of(contact)
    email_ok, phone_ok = _email_verified(user, contact), _phone_verified(contact)
    policy = _policy(db, user)
    channels = _channels()
    can_reset = bool(user.active) and _password_login(policy)
    return {
        "user_id": user.id, "username": user.username, "display_name": user.display_name, "active": bool(user.active),
        "email": user.email or None, "email_verified": email_ok,
        "email_verified_at": iso(contact.email_verified_at) if email_ok and contact else None,
        "phone": phone, "phone_display": sms.format_phone(phone) if phone else None,
        "phone_masked": sms.mask_phone(phone) if phone else None, "phone_verified": phone_ok,
        "phone_verified_at": iso(contact.phone_verified_at) if phone_ok and contact else None,
        "has_password": bool(user.password_hash), "password_login": _password_login(policy),
        "reset_channels": _reset_channels(policy), "channels": channels,
        "can_send_reset": {"email": can_reset and email_ok and _sendable_email(user) and channels["email"],
                           "sms": can_reset and phone_ok and channels["sms"]},
        "code_minutes": _minutes(), "dev_outbox": auth_messages.dev_outbox_enabled(),
    }


# =========================================================================== Eigenes Konto
@router.get("/me/contact")
def my_contact(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eigene Kontaktdaten für die Wiederherstellung (Nummer maskiert)."""
    return _my_contact(db, _get_user(db, user.id))


@router.post("/me/contact/email")
def start_email(body: EmailStart, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Neue (oder noch unbestätigte) E-Mail-Adresse: Code + Link an diese Adresse senden."""
    _session_only(user)
    row = _get_user(db, user.id)
    ip = client_ip(request)
    address = body.email.strip()
    if not auth_messages.valid_email(address):
        raise HTTPException(422, "Bitte eine gültige E-Mail-Adresse angeben.")
    if not auth_messages.email_available():
        raise HTTPException(409, "Der E-Mail-Versand ist auf diesem Server nicht eingerichtet. Bitte wenden Sie sich "
                                 "an das Sekretariat.")
    _check_password(db, row, body.password, ip)
    if address.lower() == (row.email or "").strip().lower() and _email_verified(row, _contact(db, row.id)):
        raise HTTPException(409, "Diese E-Mail-Adresse ist bereits bestätigt.")
    _limit_codes(db, row.id, "verify_email", ip)
    code_row, code, token = _issue(db, row.id, "verify_email", "email", ip, target=address, with_token=True)
    _send_verify_email(db, row, address, code, token)
    audit(db, user, "contact.email_code", f"user:{row.id}", {"target": auth_messages.mask_email(address)}, ip=ip)
    db.commit()
    return {"ok": True, "sent_to": address, "expires_at": iso(code_row.expires_at), **_my_contact(db, row)}


@router.post("/me/contact/phone")
def start_phone(body: PhoneStart, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Neue Handynummer: Code per SMS an diese Nummer senden."""
    _session_only(user)
    row = _get_user(db, user.id)
    ip = client_ip(request)
    number = sms.normalize_phone(body.phone)
    if number is None:
        raise HTTPException(422, "Bitte eine gültige Handynummer mit Vorwahl angeben, z. B. 0171 1234567 oder "
                                 "+49 171 1234567.")
    if not auth_messages.sms_available():
        raise HTTPException(409, "Der SMS-Versand ist auf diesem Server nicht eingerichtet. Bitte wenden Sie sich "
                                 "an das Sekretariat.")
    _check_password(db, row, body.password, ip)
    contact = _contact(db, row.id)
    if _phone_verified(contact) and _phone_of(contact) == number:
        raise HTTPException(409, "Diese Handynummer ist bereits bestätigt.")
    _limit_codes(db, row.id, "verify_phone", ip)
    code_row, code, _ = _issue(db, row.id, "verify_phone", "sms", ip, target=number)
    _send_verify_sms(db, number, code)
    audit(db, user, "contact.phone_code", f"user:{row.id}", {"target": sms.mask_phone(number)}, ip=ip)
    db.commit()
    return {"ok": True, "sent_to": sms.mask_phone(number), "expires_at": iso(code_row.expires_at),
            **_my_contact(db, row)}


def _apply(db: Session, actor: Any, row: User, code_row: AuthCode, ip: str | None) -> None:
    """Bestätigten Code anwenden: neue Adresse/Nummer übernehmen und als bestätigt markieren."""
    target = _target_of(code_row)
    if not target:
        raise HTTPException(400, BAD_CODE)
    contact = _contact(db, row.id, create=True)
    assert contact is not None
    code_row.used_at = utcnow()
    if code_row.purpose == "verify_email":
        old = (row.email or "").strip()
        old_verified = _email_verified(row, contact)
        row.email = target
        _set_email_verified(row, contact, True)
        if old_verified and old.lower() != target.lower():
            _notify_old_email(db, row, old, "die E-Mail-Adresse geändert")
        audit(db, actor, "contact.email_verified", f"user:{row.id}",
              {"target": auth_messages.mask_email(target), "changed": old.lower() != target.lower()}, ip=ip)
    else:
        _set_phone(contact, target, verified=True)
        if _email_verified(row, contact):
            _notify_old_email(db, row, (row.email or "").strip(), "eine neue Handynummer bestätigt")
        audit(db, actor, "contact.phone_verified", f"user:{row.id}", {"target": sms.mask_phone(target)}, ip=ip)


@router.post("/me/contact/verify")
def verify_contact(body: VerifyBody, request: Request, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Code aus E-Mail/SMS prüfen (höchstens 5 Versuche je Code)."""
    _session_only(user)
    row = _get_user(db, user.id)
    ip = client_ip(request)
    purpose = "verify_email" if body.kind == "email" else "verify_phone"
    code_row = _active_code(db, row.id, purpose)
    if code_row is None:
        raise HTTPException(400, "Kein gültiger Code – bitte einen neuen anfordern.")
    code = _clean_code(body.code)
    code_id, code_hash = code_row.id, code_row.code_hash or ""
    attempts = _take_attempt(db, code_id)
    db.commit()
    if attempts is None:
        raise HTTPException(400, "Kein gültiger Code – bitte einen neuen anfordern.")
    if len(code) != CODE_DIGITS or not hmac.compare_digest(_code_hash(purpose, row.id, code), code_hash):
        left = MAX_ATTEMPTS - attempts
        if left <= 0:
            _claim(db, code_id)
            db.commit()
        raise HTTPException(400, f"Der Code ist falsch. Noch {left} Versuch(e)." if left > 0
                            else "Der Code ist falsch. Bitte fordern Sie einen neuen an.")
    if not _claim(db, code_id):
        raise HTTPException(400, "Kein gültiger Code – bitte einen neuen anfordern.")
    _apply(db, user, row, code_row, ip)
    db.commit()
    return _my_contact(db, row)


@router.post("/me/contact/confirm-link")
def confirm_link(body: TokenBody, request: Request, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    """Bestätigungslink aus der E-Mail (``/profil?kontakt=<token>``) – nur für das eigene Konto."""
    _session_only(user)
    row = _get_user(db, user.id)
    now = utcnow()
    code_row = db.scalar(select(AuthCode).where(AuthCode.token_hash == hash_token(body.token.strip()),
                                                AuthCode.purpose == "verify_email", AuthCode.used_at.is_(None),
                                                AuthCode.expires_at > now, AuthCode.attempts < MAX_ATTEMPTS))
    if code_row is None or code_row.user_id != row.id:
        raise HTTPException(400, "Der Link ist ungültig, abgelaufen oder gehört zu einem anderen Konto.")
    _apply(db, user, row, code_row, client_ip(request))
    db.commit()
    return _my_contact(db, row)


@router.post("/me/contact/{kind}/remove")
def remove_contact(kind: Literal["email", "phone"], body: PasswordBody, request: Request,
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """E-Mail-Adresse bzw. Handynummer entfernen (aktuelles Passwort nötig, falls gesetzt)."""
    _session_only(user)
    row = _get_user(db, user.id)
    ip = client_ip(request)
    _check_password(db, row, body.password, ip)
    contact = _contact(db, row.id, create=True)
    assert contact is not None
    purpose = "verify_email" if kind == "email" else "verify_phone"
    db.execute(update(AuthCode).where(AuthCode.user_id == row.id, AuthCode.purpose == purpose,
                                      AuthCode.used_at.is_(None)).values(used_at=utcnow()))
    if kind == "email":
        row.email = None
        _set_email_verified(row, contact, False)
    else:
        _set_phone(contact, None, verified=False)
    audit(db, user, f"contact.{kind}_remove", f"user:{row.id}", ip=ip)
    db.commit()
    return _my_contact(db, row)


# =========================================================================== Verwaltung
def _check_manage(actor: AuthUser, role: str) -> None:
    from .users import _check_manage as check

    check(actor, role)


@router.get("/users/{user_id}/contact")
def admin_get_contact(user_id: int, actor: AuthUser = Depends(require("users.manage")),
                      db: Session = Depends(get_db)) -> dict:
    target = _get_user(db, user_id)
    _check_manage(actor, target.role)
    return _admin_contact(db, target)


@router.put("/users/{user_id}/contact")
def admin_put_contact(user_id: int, body: AdminContactBody, request: Request,
                      actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    """Kontakt setzen/als bestätigt markieren/entfernen. Nur übergebene Felder werden geändert."""
    target = _get_user(db, user_id)
    _check_manage(actor, target.role)
    fields = body.model_dump(exclude_unset=True)
    contact = _contact(db, target.id, create=True)
    assert contact is not None
    changes: dict[str, Any] = {}
    if "email" in fields:
        address = (fields["email"] or "").strip()
        if address and not auth_messages.valid_email(address):
            raise HTTPException(422, "Bitte eine gültige E-Mail-Adresse angeben.")
        if address.lower() != (target.email or "").strip().lower():
            target.email = address or None
            _set_email_verified(target, contact, False)
            changes["email"] = "geändert" if address else "entfernt"
        elif address != (target.email or ""):
            target.email = address or None  # nur Schreibweise
    if fields.get("email_verified") is not None:
        wanted = bool(fields["email_verified"])
        if wanted and not target.email:
            raise HTTPException(422, "Keine E-Mail-Adresse hinterlegt.")
        if wanted and not _sendable_email(target):
            raise HTTPException(422, "Die hinterlegte E-Mail-Adresse ist ungültig – bitte zuerst korrigieren.")
        if wanted != _email_verified(target, contact):
            _set_email_verified(target, contact, wanted)
            changes["email_verified"] = wanted
    if "phone" in fields:
        raw = (fields["phone"] or "").strip()
        if not raw:
            if contact.phone_enc:
                _set_phone(contact, None, verified=False)
                changes["phone"] = "entfernt"
        else:
            number = sms.normalize_phone(raw)
            if number is None:
                raise HTTPException(422, "Bitte eine gültige Handynummer mit Vorwahl angeben, z. B. 0171 1234567.")
            if number != _phone_of(contact):
                _set_phone(contact, number, verified=False)
                changes["phone"] = "gesetzt"
    if fields.get("phone_verified") is not None:
        wanted = bool(fields["phone_verified"])
        if wanted and not contact.phone_enc:
            raise HTTPException(422, "Keine Handynummer hinterlegt.")
        if wanted != _phone_verified(contact):
            contact.phone_verified_at = utcnow() if wanted else None
            contact.updated_at = utcnow()
            changes["phone_verified"] = wanted
    if changes:
        audit(db, actor, "user.contact_update", f"user:{target.id}", {"username": target.username, "changes": changes},
              ip=client_ip(request))
    db.commit()
    return _admin_contact(db, target)


@router.post("/users/{user_id}/send-reset")
def admin_send_reset(user_id: int, body: SendResetBody, request: Request,
                     actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    """Link (E-Mail) bzw. Code (SMS) zum Zurücksetzen an den **bestätigten** Kontakt des Kontos senden."""
    target = _get_user(db, user_id)
    _check_manage(actor, target.role)
    if not target.active:
        raise HTTPException(409, "Das Konto ist deaktiviert.")
    if not _password_login(_policy(db, target)):
        raise HTTPException(409, "Für dieses Konto ist die Anmeldung mit Passwort laut Anmelde-Richtlinie nicht "
                                 "erlaubt.")
    contact = _contact(db, target.id)
    if body.channel == "email":
        if not _email_verified(target, contact) or not _sendable_email(target):
            raise HTTPException(409, "Für dieses Konto ist keine bestätigte E-Mail-Adresse hinterlegt.")
        if not auth_messages.email_available():
            raise HTTPException(409, "Der E-Mail-Versand ist auf diesem Server nicht eingerichtet.")
    else:
        if not _phone_verified(contact):
            raise HTTPException(409, "Für dieses Konto ist keine bestätigte Handynummer hinterlegt.")
        if not auth_messages.sms_available():
            raise HTTPException(409, "Der SMS-Versand ist auf diesem Server nicht eingerichtet.")
    if _count(db, AuthCode.user_id == target.id, AuthCode.purpose == "reset",
              AuthCode.created_at > utcnow() - RL_WINDOW) >= ADMIN_SENDS_PER_USER_HOUR:
        raise HTTPException(429, TOO_MANY, headers={"Retry-After": "3600"})
    ip = client_ip(request)
    code_row, masked = _send_reset(db, target, body.channel, ip)
    audit(db, actor, "user.send_reset", f"user:{target.id}", {"username": target.username, "channel": body.channel},
          ip=ip)
    db.commit()
    return {"ok": True, "channel": body.channel, "sent_to": masked, "expires_at": iso(code_row.expires_at),
            "dev_outbox": auth_messages.dev_outbox_enabled()}


# =========================================================================== „Passwort vergessen“
async def _padded(fn: Callable[..., Any], *args: Any) -> Any:
    """Führt ``fn`` im Threadpool aus und antwortet frühestens nach :data:`MIN_RESPONSE_SECONDS` (auch bei Fehlern)."""
    started = time.monotonic()
    try:
        return await run_in_threadpool(fn, *args)
    finally:
        remaining = MIN_RESPONSE_SECONDS - (time.monotonic() - started)
        if remaining > 0:
            await asyncio.sleep(remaining + secrets.randbelow(40) / 1000)


def _find_accounts(db: Session, ident: str) -> list[User]:
    """Konten zur Kennung: Benutzername, **bestätigte** E-Mail-Adresse oder **bestätigte** Handynummer (aktiv)."""
    found: dict[int, User] = {}
    if ident and "@" not in ident and not ident.startswith("+"):
        user = db.scalar(select(User).where(func.lower(User.username) == ident))
        if user is not None:
            found[user.id] = user
    if "@" in ident:
        for user in db.scalars(select(User).join(UserContact, UserContact.user_id == User.id)
                               .where(func.lower(User.email) == ident, UserContact.email_verified_value == ident)
                               .order_by(User.id).limit(MAX_ACCOUNTS_PER_IDENT)):
            found.setdefault(user.id, user)
    if ident.startswith("+"):
        for user in db.scalars(select(User).join(UserContact, UserContact.user_id == User.id)
                               .where(UserContact.phone_hash == sms.phone_hash(ident),
                                      UserContact.phone_verified_at.is_not(None))
                               .order_by(User.id).limit(MAX_ACCOUNTS_PER_IDENT)):
            found.setdefault(user.id, user)
    return [u for u in found.values() if u.active][:MAX_ACCOUNTS_PER_IDENT]


def _reset_possible(db: Session, user: User, channel: str) -> bool:
    if channel not in _reset_channels(_policy(db, user)):
        return False
    contact = _contact(db, user.id)
    if channel == "email":
        return _email_verified(user, contact) and _sendable_email(user) and auth_messages.email_available()
    return _phone_verified(contact) and bool(_phone_of(contact)) and auth_messages.sms_available()


def _pick_channel(db: Session, user: User, ident: str, channel: str) -> str | None:
    """Kanal für das Zurücksetzen. ``auto``: E-Mail-Kennung → E-Mail, Nummer → SMS, Benutzername → E-Mail, sonst SMS."""
    if channel != "auto":
        return channel if _reset_possible(db, user, channel) else None
    order = ["email", "sms"] if "@" in ident else ["sms", "email"] if ident.startswith("+") else ["email", "sms"]
    return next((c for c in order if _reset_possible(db, user, c)), None)


def _do_request(identifier: str, channel: str, ip: str | None) -> dict:
    with session_scope() as db:
        now = utcnow()
        since = now - RL_WINDOW
        ident = _normalize_ident(identifier)
        ih = _ident_hash(ident)
        if _count(db, AuthCode.purpose == "rl_reset", AuthCode.ident_hash == ih,
                  AuthCode.created_at > since) >= RESET_PER_IDENT_HOUR or \
                (ip and _count(db, AuthCode.purpose == "rl_reset", AuthCode.ip == ip,
                               AuthCode.created_at > since) >= RESET_PER_IP_HOUR):
            raise HTTPException(429, TOO_MANY, headers={"Retry-After": "3600"})
        db.add(AuthCode(purpose="rl_reset", channel=channel, ident_hash=ih, ip=ip, expires_at=now + RL_WINDOW,
                        attempts=0, created_at=now))
        for user in _find_accounts(db, ident):
            use = _pick_channel(db, user, ident, channel)
            if use is None:
                continue
            # je Konto begrenzt (Benutzername, E-Mail und Nummer sind verschiedene Kennungen) – still, ohne 429
            if _count(db, AuthCode.user_id == user.id, AuthCode.purpose == "reset",
                      AuthCode.created_at > since) >= RESET_PER_USER_HOUR:
                continue
            try:
                _send_reset(db, user, use, ip, ident_hash=ih)
            except ValueError:  # nicht zustellbar: gleiche Antwort wie für unbekannte Kennungen
                log.warning("Zurücksetzen für Konto %s nicht zustellbar (%s)", user.id, use)
                continue
            audit(db, user, "auth.password_reset_request", f"user:{user.id}", {"channel": use}, ip=ip)
        db.commit()
    return {"ok": True, "message": GENERIC_RESET_REPLY, "code_minutes": _minutes(),
            "dev_outbox": auth_messages.dev_outbox_enabled()}


def _fail(db: Session, ip: str | None, detail: str) -> HTTPException:
    now = utcnow()
    db.add(AuthCode(purpose="rl_fail", ip=ip, expires_at=now + RL_WINDOW, attempts=0, created_at=now))
    db.commit()
    return HTTPException(400, detail)


def _do_verify(body: ResetVerifyBody, ip: str | None) -> dict:
    with session_scope() as db:
        now = utcnow()
        if ip and _count(db, AuthCode.purpose == "rl_fail", AuthCode.ip == ip,
                         AuthCode.created_at > now - RL_WINDOW) >= FAILS_PER_IP_HOUR:
            raise HTTPException(429, TOO_MANY, headers={"Retry-After": "3600"})
        found: AuthCode | None = None
        via = "link"
        if body.token:
            found = db.scalar(select(AuthCode).where(AuthCode.token_hash == hash_token(body.token.strip()),
                                                     AuthCode.purpose == "reset", AuthCode.used_at.is_(None),
                                                     AuthCode.expires_at > now, AuthCode.attempts < MAX_ATTEMPTS))
            if found is None:
                raise _fail(db, ip, BAD_LINK)
        elif body.identifier and body.code:
            via = "code"
            code = _clean_code(body.code)
            ids = [u.id for u in _find_accounts(db, _normalize_ident(body.identifier))]
            candidates = list(db.scalars(select(AuthCode).where(
                AuthCode.user_id.in_(ids or [-1]), AuthCode.purpose == "reset", AuthCode.used_at.is_(None),
                AuthCode.expires_at > now, AuthCode.attempts < MAX_ATTEMPTS)))
            for row in candidates:
                # Versuch zuerst atomar verbuchen – sonst ließen sich mit parallelen Anfragen beliebig viele Codes raten
                if _take_attempt(db, row.id) is None:
                    continue
                if len(code) == CODE_DIGITS and hmac.compare_digest(_code_hash("reset", row.user_id or 0, code),
                                                                    row.code_hash or ""):
                    found = row
            spent = [r.id for r in candidates if r is not found]
            db.execute(update(AuthCode).where(AuthCode.id.in_(spent or [-1]), AuthCode.attempts >= MAX_ATTEMPTS,
                                              AuthCode.used_at.is_(None))
                       .values(used_at=now).execution_options(synchronize_session=False))
            db.commit()
            if found is None:
                raise _fail(db, ip, BAD_CODE)
        else:
            raise HTTPException(422, "Bitte den Code mit Kennung oder den Link aus der E-Mail angeben.")
        user = db.get(User, found.user_id) if found.user_id else None
        if user is None or not user.active or not _password_login(_policy(db, user)) or not _claim(db, found.id):
            raise _fail(db, ip, BAD_LINK if via == "link" else BAD_CODE)
        reset_token = new_token(32)
        expires = now + timedelta(minutes=_minutes())
        db.add(AuthCode(user_id=user.id, purpose="reset_token", channel=found.channel,
                        token_hash=hash_token(reset_token), expires_at=expires, attempts=0, ip=ip, created_at=now))
        audit(db, user, "auth.password_reset_verify", f"user:{user.id}", {"channel": found.channel, "via": via},
              ip=ip)
        db.commit()
        return {"reset_token": reset_token, "username": user.username, "display_name": user.display_name,
                "min_length": min_length(user.role), "expires_at": iso(expires)}


@router.get("/auth/capabilities")
@router.get("/auth/password-reset/options")
def reset_options(db: Session = Depends(get_db)) -> dict:
    """Was der Server kann (E-Mail/SMS) und welche Rollen „Passwort vergessen“ selbst nutzen dürfen – öffentlich,
    ohne Geheimnisse, nicht kontobezogen."""
    return _capabilities(db)


@router.post("/auth/password-reset/request")
async def reset_request(body: ResetRequestBody, request: Request) -> dict:
    """„Passwort vergessen“: Code/Link anfordern. Antwort immer gleich (keine Konto-Erkennung)."""
    return await _padded(_do_request, body.identifier, body.channel, client_ip(request))


@router.post("/auth/password-reset/verify")
async def reset_verify(body: ResetVerifyBody, request: Request) -> dict:
    """Link-Token oder Kennung + Code prüfen → kurzlebiges ``reset_token``."""
    return await _padded(_do_verify, body, client_ip(request))


@router.post("/auth/password-reset/confirm")
def reset_confirm(body: ResetConfirmBody, request: Request, db: Session = Depends(get_db)) -> dict:
    """Neues Passwort setzen: Passwortregeln, alle Sitzungen beendet, Passwortwechsel-Zwang aufgehoben, 2FA bleibt."""
    ip = client_ip(request)
    now = utcnow()
    row = db.scalar(select(AuthCode).where(AuthCode.token_hash == hash_token(body.reset_token.strip()),
                                           AuthCode.purpose == "reset_token", AuthCode.used_at.is_(None),
                                           AuthCode.expires_at > now))
    user = db.get(User, row.user_id) if row is not None and row.user_id else None
    if row is None or user is None or not user.active:
        raise HTTPException(400, "Die Zeit zum Zurücksetzen ist abgelaufen. Bitte fordern Sie einen neuen Code an.")
    if not _password_login(_policy(db, user)):
        raise HTTPException(409, "Für dieses Konto ist die Anmeldung mit Passwort nicht erlaubt.")
    problems = password_problems(body.new_password, user.role, user.username)
    if problems:
        raise HTTPException(422, " ".join(problems))
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    from ..letters import clear_initial
    clear_initial(db, user.id)                     # das Startpasswort ist ersetzt (S-06)
    db.execute(update(AuthCode).where(AuthCode.user_id == user.id, AuthCode.purpose.in_(("reset", "reset_token")),
                                      AuthCode.used_at.is_(None)).values(used_at=now))
    revoked = revoke_sessions(db, user.id)
    # Erfolgreicher Nachweis über den bestätigten Kontakt hebt eine Anmeldesperre nach Fehlversuchen auf
    db.add(LoginAttempt(username=user.username.lower()[:80], ip=ip, success=True, created_at=now))
    audit(db, user, "auth.password_reset", f"user:{user.id}", {"channel": row.channel, "revoked_sessions": revoked},
          ip=ip)
    db.commit()
    return {"ok": True, "username": user.username}


# =========================================================================== Test-Postausgang
def _require_dev_outbox() -> None:
    if not auth_messages.dev_outbox_enabled():
        raise HTTPException(404, "Nicht gefunden")


@router.get("/dev-outbox")
def dev_outbox(db: Session = Depends(get_db)) -> dict:
    """Test-Postausgang (nur ``SM_DEV_OUTBOX``): die letzten 50 E-Mails/SMS, die verschickt worden wären."""
    _require_dev_outbox()
    return {"enabled": True, "hours": auth_messages.DEV_OUTBOX_HOURS,
            "items": auth_messages.dev_outbox_messages(db)}


@router.get("/dev-outbox/{message_id}/attachments/{index}")
def dev_outbox_attachment(message_id: int, index: int, db: Session = Depends(get_db)) -> Response:
    """Anhang einer Test-E-Mail herunterladen (immer als Download, ``nosniff``)."""
    _require_dev_outbox()
    att = auth_messages.dev_outbox_attachment(db, message_id, index)
    if att is None:
        raise HTTPException(404, "Nicht gefunden")
    from ..files import content_disposition

    ctype = att["content_type"] if att["content_type"] in SAFE_ATTACHMENT_TYPES else "application/octet-stream"
    return Response(content=att["data"], media_type=ctype, headers={
        "Content-Disposition": content_disposition(att["filename"]), "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "sandbox; default-src 'none'", "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer"})


# =========================================================================== Wartung
def cleanup(now: datetime | None = None) -> dict[str, int]:
    """Abgelaufene Codes/Token/Rate-Limit-Zeilen (eine Stunde Karenz) und alte Test-Nachrichten löschen."""
    now = now or utcnow()
    with session_scope() as db:
        codes = db.execute(delete(AuthCode).where(AuthCode.expires_at < now - RL_WINDOW)).rowcount or 0
    return {"auth_codes": int(codes), "dev_outbox": auth_messages.purge_dev_outbox(now)}
