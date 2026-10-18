"""Verbundene E-Mail-Konten im Postfach (Konten verwalten, Google/Microsoft-Anmeldung, Abruf, Versand an Externe).

* ``GET  /mail/providers`` – Anbieter mit Voreinstellungen und ob die Anmeldung über Google/Microsoft eingerichtet ist
* ``GET  /mail/accounts`` · ``POST /mail/accounts`` (App-Passwort; Verbindung wird vorher geprüft)
* ``PATCH /mail/accounts/{id}`` (Name, Abruf an/aus, Standard, neues Passwort) · ``DELETE /mail/accounts/{id}``
* ``POST /mail/accounts/{id}/sync`` – sofort abrufen
* ``GET  /mail/oauth/{provider}/start`` → ``{url}`` · ``GET /mail/oauth/callback`` (Weiterleitung des Anbieters)

Eingehende E-Mails werden als Unterhaltung (``kind="email"``) bzw. als Antwort in der passenden Unterhaltung abgelegt
(Zuordnung über ``Message-ID``/``In-Reply-To``). Versand an Externe: :func:`deliver_external` (aus dem Postfach).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from schulmanager.server import crypto, files, mailbridge as mb
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, session_scope, utcnow
from schulmanager.server.deps import AuthUser, client_ip, current_user, require
from schulmanager.server.events import bus
from schulmanager.server.feature_models.mail import MailAccount
from schulmanager.server.feature_models.messages import Conversation, ConversationParticipant, Message

log = logging.getLogger("schulmanager.mail")

router = APIRouter(tags=["Postfach – E-Mail-Konten"])

USE = "messages.use"
PURPOSE = "message"
REF_TYPE = "message"
MAX_ACCOUNTS = 5
EMAIL_RE = re.compile(r"^[^@\s<>\"',;]+@[^@\s<>\"',;]+\.[^@\s<>\"',;]+$")


def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value or "")) and len(value) <= 254


# =========================================================================== Zugangsdaten
def creds_for(acc: MailAccount) -> mb.Creds:
    try:
        secret = json.loads(crypto.decrypt_text(acc.secret_enc, acc.secret_aad)) if acc.secret_enc else {}
    except Exception:  # noqa: BLE001 - beschädigt/fremder Schlüssel
        raise mb.MailError("Gespeicherte Zugangsdaten sind nicht lesbar – bitte das Konto neu verbinden") from None
    return mb.Creds(email=acc.email, username=acc.username or acc.email, auth=acc.auth, secret=secret,
                    imap=(acc.imap_host, acc.imap_port), smtp=(acc.smtp_host, acc.smtp_port, acc.smtp_security),
                    provider=acc.provider, display_name=acc.display_name)


def store_secret(acc: MailAccount, secret: dict[str, Any]) -> None:
    acc.secret_enc = crypto.encrypt_text(json.dumps(secret), acc.secret_aad)


def _persist_refresh(db: Session, acc: MailAccount, c: mb.Creds) -> None:
    if c.changed:
        store_secret(acc, c.secret)
        c.changed = False


def account_out(acc: MailAccount) -> dict[str, Any]:
    p = mb.PROVIDERS.get(acc.provider)
    return {"id": acc.id, "provider": acc.provider, "provider_label": p.label if p else acc.provider,
            "email": acc.email, "display_name": acc.display_name, "auth": acc.auth,
            "imap_host": acc.imap_host, "imap_port": acc.imap_port, "smtp_host": acc.smtp_host,
            "smtp_port": acc.smtp_port, "smtp_security": acc.smtp_security, "sync_enabled": acc.sync_enabled,
            "is_default": acc.is_default, "last_sync_at": iso(acc.last_sync_at), "last_error": acc.last_error or None,
            "created_at": iso(acc.created_at)}


def accounts_of(db: Session, user_id: int) -> list[MailAccount]:
    return list(db.scalars(select(MailAccount).where(MailAccount.user_id == user_id)
                           .order_by(MailAccount.is_default.desc(), MailAccount.id)))


def sending_account(db: Session, user_id: int, preferred: Optional[int] = None) -> Optional[MailAccount]:
    """Konto für den Versand: gewünschtes (falls eigenes), sonst Standard, sonst das erste."""
    accs = accounts_of(db, user_id)
    if preferred:
        for a in accs:
            if a.id == preferred:
                return a
    return accs[0] if accs else None


# =========================================================================== Versand an Externe
def deliver_external(db: Session, conv: Conversation, msg: Message, sender_id: int, *, subject: str, text: str,
                     preferred_account: Optional[int] = None) -> dict[str, Any]:
    """Schickt ``msg`` per E-Mail an die externen Beteiligten der Unterhaltung (über das Konto der absendenden
    Person) und speichert Versandstatus + Message-ID an der Nachricht. Ohne Commit. Wirft nie."""
    ext = [e for e in (conv.external or []) if isinstance(e, dict) and e.get("email")]
    if not ext:
        return {"status": "none"}
    acc = sending_account(db, sender_id, preferred_account or conv.mail_account_id)
    now = iso(utcnow())
    if acc is None:
        msg.delivery = {"status": "no_account", "at": now, "to": [e["email"] for e in ext],
                        "error": "Kein E-Mail-Konto verbunden – externe Empfänger/innen haben die Nachricht nicht "
                                 "erhalten"}
        return msg.delivery
    to = [(e.get("name") or "", e["email"]) for e in ext if e.get("role") in ("to", "from")]
    cc = [(e.get("name") or "", e["email"]) for e in ext if e.get("role") == "cc"]
    bcc = [e["email"] for e in ext if e.get("role") == "bcc"]
    own = acc.email.lower()
    to = [x for x in to if x[1].lower() != own]
    cc = [x for x in cc if x[1].lower() != own]
    bcc = [x for x in bcc if x.lower() != own]
    if not to and not cc and not bcc:
        return {"status": "none"}
    refs = [r for r in db.scalars(select(Message.mail_message_id).where(
        Message.conversation_id == conv.id, Message.mail_message_id.is_not(None), Message.id != msg.id)
        .order_by(Message.id)) if r]
    mid = mb.new_message_id(acc.email)
    attachments = []
    for fid in msg.attachment_ids or []:
        meta = files.get_file(db, fid)
        if meta is not None:
            try:
                attachments.append((meta.filename, meta.content_type or "application/octet-stream",
                                    files.read_bytes(meta)))
            except Exception:  # noqa: BLE001
                log.warning("Anhang %s konnte nicht gelesen werden", fid)
    status: dict[str, Any] = {"status": "sent", "at": now, "to": [x[1] for x in to + cc] + bcc,
                              "account": acc.email}
    try:
        c = creds_for(acc)
        mail = mb.build_mail(c, to=to, cc=cc, subject=subject, text=text, message_id=mid,
                             in_reply_to=refs[-1] if refs else None, references=refs, attachments=attachments)
        mb.transport.send(c, mail, [x[1] for x in to + cc] + bcc)
        _persist_refresh(db, acc, c)
        msg.mail_message_id = mid
    except mb.MailError as exc:
        status.update(status="failed", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        log.exception("E-Mail-Versand fehlgeschlagen")
        status.update(status="failed", error=f"Versand fehlgeschlagen ({type(exc).__name__})")
    msg.delivery = status
    if conv.mail_account_id is None:
        conv.mail_account_id = acc.id
    return status


# =========================================================================== Empfang
def _known_conversation(db: Session, owner_id: int, refs: list[str]) -> Optional[Conversation]:
    if not refs:
        return None
    rows = db.execute(select(Message.conversation_id).join(
        ConversationParticipant, ConversationParticipant.conversation_id == Message.conversation_id)
        .where(Message.mail_message_id.in_(refs[-50:]), ConversationParticipant.user_id == owner_id)
        .order_by(Message.id.desc()).limit(1)).first()
    return db.get(Conversation, rows[0]) if rows else None


def import_mail(db: Session, acc: MailAccount, parsed: mb.ParsedMail) -> Optional[int]:
    """Legt eine eingegangene E-Mail ins Postfach von ``acc.user_id``. Liefert die Unterhaltungs-ID (oder ``None``,
    wenn übersprungen: eigene Absendeadresse oder schon vorhanden)."""
    own = acc.email.lower()
    if parsed.from_addr.lower() == own:
        return None
    if parsed.message_id and db.scalar(select(Message.id).join(
            ConversationParticipant, ConversationParticipant.conversation_id == Message.conversation_id)
            .where(Message.mail_message_id == parsed.message_id, ConversationParticipant.user_id == acc.user_id)
            .limit(1)):
        return None
    now = utcnow()
    conv = _known_conversation(db, acc.user_id, parsed.in_reply_to)
    new_conv = conv is None
    if new_conv:
        ext = [{"email": parsed.from_addr, "name": parsed.from_name, "role": "from"}]
        seen = {parsed.from_addr, own}
        for role, lst in (("to", parsed.to), ("cc", parsed.cc)):
            for name, addr in lst:
                if addr not in seen:
                    seen.add(addr)
                    ext.append({"email": addr, "name": name, "role": "cc" if role == "cc" else "to"})
        conv = Conversation(kind="email", allow_replies="all", created_by=None, created_at=now, audience=None,
                            recipient_count=1, last_message_id=0, last_message_at=now, subject_enc="",
                            external=ext, mail_account_id=acc.id)
        db.add(conv)
        db.flush()
        conv.subject_enc = crypto.encrypt_text((parsed.subject or "")[:300], conv.subject_aad)
        db.add(ConversationParticipant(conversation_id=conv.id, user_id=acc.user_id, joined_at=now,
                                       has_incoming=True, recipient_role="to"))
    else:
        ext = list(conv.external or [])
        if parsed.from_addr not in {e.get("email") for e in ext}:
            ext.append({"email": parsed.from_addr, "name": parsed.from_name, "role": "to"})
            conv.external = ext
    msg = Message(conversation_id=conv.id, sender_id=None, body_enc="", attachment_ids=[], created_at=now,
                  external_from=parsed.from_addr[:254], external_name=(parsed.from_name or "")[:200],
                  mail_message_id=parsed.message_id or None)
    db.add(msg)
    db.flush()
    msg.body_enc = crypto.encrypt_text(parsed.text or "", msg.body_aad)
    ids = []
    for name, ctype, data in parsed.attachments:
        try:
            meta = files.store_bytes(db, None, data, name, ctype, purpose=PURPOSE)
            files.attach(db, meta.id, None, REF_TYPE, msg.id)
            ids.append(meta.id)
        except files.FileError as exc:
            log.info("Anhang „%s“ nicht übernommen: %s", name, exc)
    msg.attachment_ids = ids
    conv.last_message_id = msg.id
    conv.last_message_at = now
    if not new_conv:
        db.execute(update(ConversationParticipant).where(ConversationParticipant.conversation_id == conv.id,
                                                         ConversationParticipant.user_id == acc.user_id)
                   .values(deleted=False, archived=False, has_incoming=True))
    return conv.id


def sync_account(db: Session, acc: MailAccount) -> int:
    """Neue E-Mails eines Kontos abrufen und ins Postfach legen. Liefert die Zahl übernommener E-Mails."""
    try:
        c = creds_for(acc)
        validity, mails = mb.transport.fetch(c, acc.uidvalidity, acc.last_uid)
        _persist_refresh(db, acc, c)
    except mb.MailError as exc:
        acc.last_error = str(exc)[:500]
        acc.last_sync_at = utcnow()
        db.commit()
        return 0
    if validity and acc.uidvalidity and validity != acc.uidvalidity:
        acc.last_uid = 0
    count = 0
    convs: set[int] = set()
    for m in mails:
        try:
            cid = import_mail(db, acc, mb.parse_mail(m.raw))
            if cid:
                count += 1
                convs.add(cid)
        except Exception:  # noqa: BLE001 - eine kaputte E-Mail darf den Abruf nicht stoppen
            log.exception("E-Mail (UID %s) konnte nicht übernommen werden", m.uid)
        acc.last_uid = max(acc.last_uid or 0, m.uid)
    acc.uidvalidity = validity or acc.uidvalidity
    acc.last_sync_at = utcnow()
    acc.last_error = ""
    db.commit()
    if count:
        bus.publish("change", {"version": None, "scope": ["messages"], "dates": []}, user_ids={acc.user_id})
        for cid in convs:
            bus.publish("message", {"conversation_id": cid, "new_message": True}, user_ids={acc.user_id})
    return count


def sync_all() -> int:
    total = 0
    with session_scope() as db:
        ids = list(db.scalars(select(MailAccount.id).where(MailAccount.sync_enabled.is_(True))))
    for aid in ids:
        with session_scope() as db:
            acc = db.get(MailAccount, aid)
            if acc is not None and acc.sync_enabled:
                total += sync_account(db, acc)
    return total


mb.sync_hook = sync_all


# =========================================================================== Endpunkte
class AccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["google", "apple", "microsoft", "gmx", "webde", "tonline", "yahoo", "custom"] = "custom"
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=500)
    display_name: str = Field("", max_length=200)
    username: str = Field("", max_length=254)
    imap_host: str = Field("", max_length=200)
    imap_port: int = Field(993, ge=1, le=65535)
    smtp_host: str = Field("", max_length=200)
    smtp_port: int = Field(587, ge=1, le=65535)
    smtp_security: Literal["ssl", "starttls"] = "starttls"


class AccountPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: Optional[str] = Field(None, max_length=200)
    sync_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=1, max_length=500)


def _own(db: Session, user: AuthUser, account_id: int) -> MailAccount:
    acc = db.get(MailAccount, account_id)
    if acc is None or acc.user_id != user.id:
        raise HTTPException(404, "E-Mail-Konto nicht gefunden")
    return acc


CUSTOM_RIGHT = "mail.custom_server"
#: Verbinden/Passwort prüfen löst eine Verbindung nach außen aus → Ratenlimit je Konto (Schutz vor Port-Scans)
CONNECT_LIMIT = (10, 3600.0)          # Versuche je Fenster (Sekunden)
_connect_hits: dict[int, list[float]] = {}


def _rate_limit(user_id: int) -> None:
    import time

    now = time.monotonic()
    hits = [t for t in _connect_hits.get(user_id, []) if now - t < CONNECT_LIMIT[1]]
    if len(hits) >= CONNECT_LIMIT[0]:
        _connect_hits[user_id] = hits
        raise HTTPException(429, "Zu viele Verbindungsversuche – bitte später erneut versuchen.")
    hits.append(now)
    _connect_hits[user_id] = hits


def _check_target(imap: tuple[str, int], smtp: tuple[str, int, str]) -> None:
    """Zielprüfung (SSRF): Auflösung, öffentliche Adressen, erlaubte Ports. Einheitliche Meldung für Nutzer."""
    from schulmanager.server import net_guard

    try:
        net_guard.check_mail_host(imap[0], imap[1], "imap")
        net_guard.check_mail_host(smtp[0], smtp[1], "smtp")
    except net_guard.BlockedTarget as exc:
        log.info("Mailserver abgelehnt (%s:%s / %s:%s): %s", imap[0], imap[1], smtp[0], smtp[1], exc.detail)
        raise HTTPException(422, "Server nicht erreichbar oder nicht zulässig – Servername, Port und "
                                 "Verschlüsselung prüfen. Interne Server muss die Administration freigeben "
                                 "(SM_OUTBOUND_ALLOW).") from None


@router.get("/mail/providers")
def providers(user: AuthUser = Depends(require(USE))) -> dict:
    out = []
    for p in mb.PROVIDERS.values():
        out.append({"id": p.id, "label": p.label, "imap_host": p.imap[0], "imap_port": p.imap[1],
                    "smtp_host": p.smtp[0], "smtp_port": p.smtp[1], "smtp_security": p.smtp[2],
                    "password_ok": p.password_ok, "oauth": bool(p.oauth and mb.oauth_app(p.oauth)),
                    "hint": p.hint, "domains": list(p.domains)})
    return {"providers": out, "redirect_uri": mb.oauth_redirect_uri(),
            "custom_allowed": CUSTOM_RIGHT in user.permissions}


@router.get("/mail/accounts")
def list_accounts(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    return {"accounts": [account_out(a) for a in accounts_of(db, user.id)], "max": MAX_ACCOUNTS}


def _create(db: Session, user: AuthUser, *, provider: str, email: str, display_name: str, auth: str, username: str,
            secret: dict[str, Any], imap: tuple[str, int], smtp: tuple[str, int, str], request: Request,
            check: bool = True) -> MailAccount:
    email = email.strip().lower()
    if not valid_email(email):
        raise HTTPException(422, "Ungültige E-Mail-Adresse")
    existing = db.scalar(select(MailAccount).where(MailAccount.user_id == user.id, MailAccount.email == email))
    if existing is None and len(accounts_of(db, user.id)) >= MAX_ACCOUNTS:
        raise HTTPException(409, f"Höchstens {MAX_ACCOUNTS} E-Mail-Konten je Person")
    if not imap[0] or not smtp[0]:
        raise HTTPException(422, "Bitte IMAP- und SMTP-Server angeben")
    if check:
        _rate_limit(user.id)
        if provider == "custom":          # feste Anbieter-Server sind vertrauenswürdig; verbunden wird ohnehin geprüft
            _check_target(imap, smtp)
    creds = mb.Creds(email=email, username=username or email, auth=auth, secret=secret, imap=imap, smtp=smtp,
                     provider=provider, display_name=display_name)
    if check:
        try:
            mb.transport.check(creds)
        except mb.MailError as exc:
            raise HTTPException(422, str(exc)) from None
    acc = existing or MailAccount(user_id=user.id, email=email, created_at=utcnow(), last_uid=0, last_error="",
                                  is_default=not accounts_of(db, user.id))
    acc.provider, acc.display_name, acc.auth, acc.username = provider, display_name, auth, username or email
    acc.imap_host, acc.imap_port = imap
    acc.smtp_host, acc.smtp_port, acc.smtp_security = smtp
    acc.sync_enabled = True
    if existing is None:
        acc.secret_enc = ""
        db.add(acc)
        db.flush()
    store_secret(acc, creds.secret)
    audit(db, user, "mail.account_connect", f"mail_account:{acc.id}", {"provider": provider, "auth": auth},
          ip=client_ip(request))
    db.commit()
    mb.kick()
    return acc


@router.post("/mail/accounts", status_code=201)
def add_account(body: AccountIn, request: Request, user: AuthUser = Depends(require(USE)),
                db: Session = Depends(get_db)) -> dict:
    """E-Mail-Konto mit (App-)Passwort verbinden. Die Anmeldung an IMAP und SMTP wird vorher geprüft."""
    p = mb.PROVIDERS[body.provider]
    if not p.password_ok:
        raise HTTPException(422, f"{p.label} erlaubt den Zugang nur über die Anmeldung beim Anbieter – bitte "
                                 "„Mit Microsoft anmelden“ verwenden")
    if body.provider == "custom":
        # Eigene Server (auch fremde Hosts/Ports) tragen nur Konten mit dem Recht ein (S-02): sonst ließe sich der
        # Server als Netzwerk-Scanner benutzen. Für bekannte Anbieter gelten immer deren feste Server.
        if CUSTOM_RIGHT not in user.permissions:
            raise HTTPException(403, "Eigene Mailserver darf nur Personal mit Freigabe eintragen – bitte einen der "
                                     "bekannten Anbieter wählen oder die Verwaltung fragen.")
        imap = (body.imap_host.strip(), body.imap_port)
        smtp = (body.smtp_host.strip(), body.smtp_port, body.smtp_security)
    else:
        imap, smtp = p.imap, p.smtp
    acc = _create(db, user, provider=body.provider, email=body.email, display_name=body.display_name.strip(),
                  auth="password", username=body.username.strip(), secret={"password": body.password},
                  imap=imap, smtp=smtp, request=request)
    return account_out(acc)


@router.patch("/mail/accounts/{account_id}")
def patch_account(account_id: int, body: AccountPatch, user: AuthUser = Depends(require(USE)),
                  db: Session = Depends(get_db)) -> dict:
    acc = _own(db, user, account_id)
    if body.display_name is not None:
        acc.display_name = body.display_name.strip()
    if body.sync_enabled is not None:
        acc.sync_enabled = body.sync_enabled
    if body.password is not None:
        if acc.auth != "password":
            raise HTTPException(422, "Dieses Konto ist über den Anbieter angemeldet – bitte neu verbinden")
        c = creds_for(acc)
        c.secret = {"password": body.password}
        _rate_limit(user.id)
        try:
            mb.transport.check(c)
        except mb.MailError as exc:
            raise HTTPException(422, str(exc)) from None
        store_secret(acc, c.secret)
        acc.last_error = ""
    if body.is_default:
        for other in accounts_of(db, user.id):
            other.is_default = other.id == acc.id
    db.commit()
    return account_out(acc)


@router.delete("/mail/accounts/{account_id}")
def delete_account(account_id: int, request: Request, user: AuthUser = Depends(require(USE)),
                   db: Session = Depends(get_db)) -> dict:
    """Konto trennen (Zugangsdaten werden gelöscht; bereits abgerufene E-Mails bleiben im Postfach)."""
    acc = _own(db, user, account_id)
    was_default = acc.is_default
    db.execute(update(Conversation).where(Conversation.mail_account_id == acc.id).values(mail_account_id=None))
    db.delete(acc)
    audit(db, user, "mail.account_remove", f"mail_account:{account_id}", {}, ip=client_ip(request))
    db.flush()
    if was_default:
        rest = accounts_of(db, user.id)
        if rest:
            rest[0].is_default = True
    db.commit()
    return {"deleted": account_id}


@router.post("/mail/accounts/{account_id}/sync")
def sync_now(account_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    acc = _own(db, user, account_id)
    n = sync_account(db, acc)
    return {"imported": n, "account": account_out(acc)}


@router.get("/mail/oauth/{provider}/start")
def oauth_start(provider: Literal["google", "microsoft"], login_hint: str = Query("", max_length=254),
                user: AuthUser = Depends(require(USE))) -> dict:
    app = mb.oauth_app(provider)
    if app is None:
        raise HTTPException(409, "Die Anmeldung über diesen Anbieter ist auf dem Server noch nicht eingerichtet "
                                 "(Administration: App beim Anbieter registrieren, siehe docs/BETRIEB.md)")
    return {"url": mb.authorize_url(app, mb.make_state(user.id, provider), login_hint)}


@router.get("/mail/oauth/callback", include_in_schema=False)
def oauth_callback(request: Request, code: str = Query("", max_length=4000), state: str = Query("", max_length=2000),
                   error: str = Query("", max_length=200), user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Rückkehr vom Anbieter: Code gegen dauerhafte Freigabe tauschen, Konto anlegen, zurück zu den Einstellungen."""
    target = "/postfach/einstellungen"
    if error or not code:
        return RedirectResponse(f"{target}?mail=abgebrochen", status_code=303)
    try:
        uid, provider = mb.read_state(state)
    except Exception:  # noqa: BLE001
        return RedirectResponse(f"{target}?mail=fehler", status_code=303)
    if uid != user.id:
        return RedirectResponse(f"{target}?mail=fehler", status_code=303)
    app = mb.oauth_app(provider)
    p = mb.PROVIDERS.get(provider)
    if app is None or p is None:
        return RedirectResponse(f"{target}?mail=fehler", status_code=303)
    try:
        got = mb.exchange_code(app, code)
        _create(db, user, provider=provider, email=got["email"], display_name=got.get("name", ""), auth="oauth2",
                username=got["email"], secret=got["secret"], imap=p.imap, smtp=p.smtp, request=request, check=False)
    except HTTPException as exc:
        log.info("OAuth-Verbindung abgelehnt: %s", exc.detail)
        return RedirectResponse(f"{target}?mail=fehler", status_code=303)
    except Exception:  # noqa: BLE001
        log.exception("OAuth-Verbindung fehlgeschlagen")
        return RedirectResponse(f"{target}?mail=fehler", status_code=303)
    return RedirectResponse(f"{target}?mail=verbunden", status_code=303)
