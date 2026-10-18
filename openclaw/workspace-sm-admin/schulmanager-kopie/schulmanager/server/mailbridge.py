"""E-Mail-Brücke des Postfachs: verbundene E-Mail-Konten (IMAP/SMTP) senden und empfangen.

* **Senden:** Nachrichten an externe Adressen (und Antworten in Unterhaltungen mit Externen) gehen über das verbundene
  Konto der absendenden Person per SMTP hinaus. Jede Nachricht bekommt eine eigene ``Message-ID``; Antworten von außen
  werden darüber (``In-Reply-To``/``References``) wieder der Unterhaltung zugeordnet.
* **Empfangen:** Ein Hintergrund-Thread ruft alle ``SM_MAIL_SYNC_MINUTES`` Minuten neue E-Mails aus dem Posteingang
  jedes Kontos ab (nur lesend, ``BODY.PEEK`` – im Postfach des Anbieters ändert sich nichts) und legt sie als
  Unterhaltung bzw. Antwort ins Postfach. Text wird verschlüsselt gespeichert, HTML nur als Text übernommen
  (keine Skripte/Bilder), Anhänge über die verschlüsselte Dateiablage.
* **Anmeldung:** App-Passwort (Google, Apple/iCloud, Yahoo, GMX, Web.de, T-Online, eigener Server) oder OAuth 2.0
  (Google, Microsoft – nur wenn die Schule eine App registriert hat: ``SM_OAUTH_GOOGLE_CLIENT_ID/SECRET``,
  ``SM_OAUTH_MICROSOFT_CLIENT_ID/SECRET``). Microsoft (Outlook/Hotmail/365) erlaubt IMAP/SMTP nur noch mit OAuth.

Zugangsdaten liegen nur verschlüsselt in ``mail_accounts.secret_enc``. Für Tests lässt sich der Transport ersetzen
(:data:`transport`).
"""
from __future__ import annotations

import base64
import email
import email.policy
import email.utils
import hashlib
import hmac
import html
import imaplib
import json
import logging
import re
import secrets
import smtplib
import ssl
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Callable, Optional

from . import net_guard

log = logging.getLogger("schulmanager.mail")

TIMEOUT = 20
MAX_FETCH = 50                  # E-Mails je Konto und Lauf
FIRST_SYNC_DAYS = 14            # erster Abruf: nur E-Mails der letzten Tage
MAX_MAIL_BYTES = 15 * 1024 * 1024
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_BODY_CHARS = 20000


# =========================================================================== Anbieter
@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    imap: tuple[str, int]
    smtp: tuple[str, int, str]               # host, port, ssl|starttls
    password_ok: bool = True                 # App-Passwort möglich
    oauth: Optional[str] = None              # google|microsoft
    hint: str = ""
    domains: tuple[str, ...] = ()


PROVIDERS: dict[str, Provider] = {p.id: p for p in (
    Provider("google", "Google (Gmail)", ("imap.gmail.com", 993), ("smtp.gmail.com", 465, "ssl"), True, "google",
             "Mit Google-Anmeldung oder einem App-Passwort (Google-Konto → Sicherheit → 2-Faktor → App-Passwörter).",
             ("gmail.com", "googlemail.com")),
    Provider("apple", "Apple (iCloud)", ("imap.mail.me.com", 993), ("smtp.mail.me.com", 587, "starttls"), True, None,
             "Apple erlaubt nur app-spezifische Passwörter: appleid.apple.com → Anmeldung und Sicherheit → "
             "App-spezifische Passwörter.", ("icloud.com", "me.com", "mac.com")),
    Provider("microsoft", "Microsoft (Outlook, Hotmail, Microsoft 365)", ("outlook.office365.com", 993),
             ("smtp.office365.com", 587, "starttls"), False, "microsoft",
             "Microsoft erlaubt E-Mail-Abruf nur noch mit Microsoft-Anmeldung (OAuth).",
             ("outlook.com", "outlook.de", "hotmail.com", "hotmail.de", "live.com", "live.de", "msn.com")),
    Provider("gmx", "GMX", ("imap.gmx.net", 993), ("mail.gmx.net", 587, "starttls"), True, None,
             "In den GMX-Einstellungen „POP3/IMAP Abruf“ erlauben.", ("gmx.de", "gmx.net", "gmx.at", "gmx.ch")),
    Provider("webde", "WEB.DE", ("imap.web.de", 993), ("smtp.web.de", 587, "starttls"), True, None,
             "In den WEB.DE-Einstellungen „POP3/IMAP Abruf“ erlauben.", ("web.de",)),
    Provider("tonline", "Telekom (T-Online)", ("secureimap.t-online.de", 993),
             ("securesmtp.t-online.de", 465, "ssl"), True, None,
             "Telekom: eigenes E-Mail-Passwort im Kundencenter anlegen.", ("t-online.de", "magenta.de")),
    Provider("yahoo", "Yahoo", ("imap.mail.yahoo.com", 993), ("smtp.mail.yahoo.com", 465, "ssl"), True, None,
             "Yahoo: Kontosicherheit → App-Passwort erstellen.", ("yahoo.com", "yahoo.de")),
    Provider("custom", "Anderer Anbieter", ("", 993), ("", 587, "starttls"), True, None,
             "IMAP- und SMTP-Server stehen in der Hilfe Ihres Anbieters."),
)}


def guess_provider(address: str) -> str:
    domain = address.rsplit("@", 1)[-1].lower().strip()
    for p in PROVIDERS.values():
        if domain in p.domains:
            return p.id
    return "custom"


# =========================================================================== OAuth 2.0
@dataclass(frozen=True)
class OAuthApp:
    provider: str
    auth_url: str
    token_url: str
    scopes: str
    client_id: str
    client_secret: str


def oauth_app(provider: str) -> Optional[OAuthApp]:
    from .config import config
    if provider == "google":
        cid, sec = getattr(config, "oauth_google_client_id", None), getattr(config, "oauth_google_client_secret", None)
        if cid and sec:
            return OAuthApp("google", "https://accounts.google.com/o/oauth2/v2/auth",
                            "https://oauth2.googleapis.com/token", "openid email https://mail.google.com/", cid, sec)
    if provider == "microsoft":
        cid = getattr(config, "oauth_microsoft_client_id", None)
        sec = getattr(config, "oauth_microsoft_client_secret", None)
        tenant = getattr(config, "oauth_microsoft_tenant", None) or "common"
        if cid and sec:
            base = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0"
            return OAuthApp("microsoft", f"{base}/authorize", f"{base}/token",
                            "openid email offline_access https://outlook.office.com/IMAP.AccessAsUser.All "
                            "https://outlook.office.com/SMTP.Send", cid, sec)
    return None


def oauth_redirect_uri() -> str:
    from .config import config
    return f"{config.base_url}/api/v1/mail/oauth/callback"


def _state_key() -> bytes:
    from .config import config
    return hashlib.sha256(("mail-oauth:" + config.secret_key).encode()).digest()


def make_state(user_id: int, provider: str) -> str:
    payload = json.dumps({"u": user_id, "p": provider, "n": secrets.token_urlsafe(8),
                          "e": int(time.time()) + 900}, separators=(",", ":")).encode()
    sig = hmac.new(_state_key(), payload, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(payload + sig).decode().rstrip("=")


def read_state(state: str) -> tuple[int, str]:
    raw = base64.urlsafe_b64decode(state + "=" * (-len(state) % 4))
    payload, sig = raw[:-16], raw[-16:]
    if not hmac.compare_digest(hmac.new(_state_key(), payload, hashlib.sha256).digest()[:16], sig):
        raise ValueError("Ungültige Anmeldung (state)")
    data = json.loads(payload)
    if int(data["e"]) < time.time():
        raise ValueError("Die Anmeldung ist abgelaufen – bitte erneut verbinden")
    return int(data["u"]), str(data["p"])


def authorize_url(app: OAuthApp, state: str, login_hint: str = "") -> str:
    params = {"client_id": app.client_id, "redirect_uri": oauth_redirect_uri(), "response_type": "code",
              "scope": app.scopes, "state": state}
    if app.provider == "google":
        params.update(access_type="offline", prompt="consent")
    else:
        params.update(prompt="select_account")
    if login_hint:
        params["login_hint"] = login_hint
    return app.auth_url + "?" + urllib.parse.urlencode(params)


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with net_guard.urlopen(req, "https", timeout=TIMEOUT) as resp:  # feste Anbieter-URL, trotzdem geprüft
        return json.loads(resp.read().decode())


def _jwt_claims(token: str) -> dict[str, Any]:
    try:
        part = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    except (IndexError, ValueError):
        return {}


def exchange_code(app: OAuthApp, code: str) -> dict[str, Any]:
    """Code → Tokens; liefert ``{"email", "name", "secret": {...}}``."""
    tok = _post_form(app.token_url, {"grant_type": "authorization_code", "code": code,
                                     "redirect_uri": oauth_redirect_uri(), "client_id": app.client_id,
                                     "client_secret": app.client_secret})
    claims = _jwt_claims(tok.get("id_token", ""))
    address = claims.get("email") or claims.get("preferred_username") or ""
    if not tok.get("refresh_token") or "@" not in address:
        raise ValueError("Der Anbieter hat keine dauerhafte Freigabe oder keine E-Mail-Adresse geliefert")
    return {"email": address.lower(), "name": claims.get("name") or "",
            "secret": {"refresh_token": tok["refresh_token"], "access_token": tok.get("access_token", ""),
                       "expires_at": int(time.time()) + int(tok.get("expires_in", 0)) - 60}}


def refresh_access(app: OAuthApp, secret: dict[str, Any]) -> dict[str, Any]:
    if secret.get("access_token") and int(secret.get("expires_at", 0)) > time.time():
        return secret
    tok = _post_form(app.token_url, {"grant_type": "refresh_token", "refresh_token": secret["refresh_token"],
                                     "client_id": app.client_id, "client_secret": app.client_secret})
    out = dict(secret)
    out["access_token"] = tok["access_token"]
    out["expires_at"] = int(time.time()) + int(tok.get("expires_in", 3600)) - 60
    if tok.get("refresh_token"):
        out["refresh_token"] = tok["refresh_token"]
    return out


# =========================================================================== Konto-Zugang
@dataclass
class Creds:
    """Entschlüsselte Zugangsdaten eines Kontos (nur im Speicher)."""
    email: str
    username: str
    auth: str                        # password|oauth2
    secret: dict[str, Any]
    imap: tuple[str, int]
    smtp: tuple[str, int, str]
    provider: str = "custom"
    display_name: str = ""
    changed: bool = False            # OAuth-Token erneuert → speichern

    def bearer(self) -> str:
        app = oauth_app(self.provider)
        if app is None:
            raise MailError("Die Anmeldung über diesen Anbieter ist auf dem Server nicht eingerichtet")
        new = refresh_access(app, self.secret)
        if new is not self.secret:
            self.secret, self.changed = new, True
        return self.secret["access_token"]


class MailError(Exception):
    """Verständliche Fehlermeldung für die Oberfläche (ohne Zugangsdaten)."""


def _xoauth2(user: str, token: str) -> str:
    return f"user={user}\x01auth=Bearer {token}\x01\x01"


def _friendly(exc: BaseException, what: str) -> MailError:
    text = str(exc)
    if isinstance(exc, (imaplib.IMAP4.error, smtplib.SMTPAuthenticationError)) or "AUTHENTICATIONFAILED" in text \
            or "535" in text:
        return MailError(f"{what}: Anmeldung abgelehnt – Adresse/App-Passwort prüfen (bei Google/Apple/Yahoo ist ein "
                         "App-Passwort nötig, nicht das normale Passwort)")
    if isinstance(exc, (TimeoutError, OSError)):
        # Einheitlich: keine Unterscheidung abgelehnt/Zeitüberschreitung/Zertifikat (sonst Port-Scan möglich)
        log.info("%s: Verbindung fehlgeschlagen (%s)", what, type(exc).__name__)
        return MailError(f"{what}: Server nicht erreichbar oder nicht zulässig – Servername, Port und "
                         "Verschlüsselung prüfen")
    return MailError(f"{what}: {text[:200]}")


# --------------------------------------------------------------------------- Transport (austauschbar für Tests)
@dataclass
class FetchedMail:
    uid: int
    raw: bytes


class Transport:
    """Echter Netzwerkzugriff per ``imaplib``/``smtplib``."""

    def imap_login(self, c: Creds) -> imaplib.IMAP4_SSL:
        ctx = ssl.create_default_context()
        try:
            conn = net_guard.imap_ssl_class()(c.imap[0], c.imap[1], ssl_context=ctx, timeout=TIMEOUT)
        except (OSError, imaplib.IMAP4.error) as exc:
            raise _friendly(exc, "IMAP") from None
        try:
            if c.auth == "oauth2":
                token = c.bearer()
                conn.authenticate("XOAUTH2", lambda _: _xoauth2(c.username or c.email, token).encode())
            else:
                conn.login(c.username or c.email, c.secret.get("password", ""))
        except (OSError, imaplib.IMAP4.error) as exc:
            try:
                conn.logout()
            except Exception:  # noqa: BLE001
                pass
            raise _friendly(exc, "IMAP") from None
        return conn

    def check(self, c: Creds) -> None:
        """Anmeldung an IMAP und SMTP prüfen (beim Verbinden)."""
        conn = self.imap_login(c)
        try:
            conn.logout()
        except Exception:  # noqa: BLE001
            pass
        with self._smtp(c):
            pass

    def _smtp(self, c: Creds) -> smtplib.SMTP:
        host, port, sec = c.smtp
        ctx = ssl.create_default_context()
        plain, secure = net_guard.smtp_classes()
        try:
            if sec == "ssl":
                s: smtplib.SMTP = secure(host, port, timeout=TIMEOUT, context=ctx)
            else:
                s = plain(host, port, timeout=TIMEOUT)
                s.starttls(context=ctx)
            if c.auth == "oauth2":
                token = c.bearer()
                s.ehlo()
                code, resp = s.docmd("AUTH", "XOAUTH2 " + base64.b64encode(
                    _xoauth2(c.username or c.email, token).encode()).decode())
                if code != 235:
                    raise smtplib.SMTPAuthenticationError(code, resp)
            else:
                s.login(c.username or c.email, c.secret.get("password", ""))
        except (OSError, smtplib.SMTPException) as exc:
            raise _friendly(exc, "SMTP") from None
        return s

    def send(self, c: Creds, msg: EmailMessage, recipients: list[str]) -> None:
        try:
            with self._smtp(c) as s:
                s.send_message(msg, from_addr=c.email, to_addrs=recipients)
        except MailError:
            raise
        except (OSError, smtplib.SMTPException) as exc:
            raise _friendly(exc, "Versand") from None

    def fetch(self, c: Creds, uidvalidity: Optional[int], last_uid: int) -> tuple[int, list[FetchedMail]]:
        """Neue E-Mails im Posteingang (UID > ``last_uid``); beim ersten Mal nur die der letzten Tage."""
        conn = self.imap_login(c)
        try:
            typ, data = conn.select("INBOX", readonly=True)
            if typ != "OK":
                raise MailError("Posteingang konnte nicht geöffnet werden")
            typ, resp = conn.response("UIDVALIDITY")
            validity = int(resp[0]) if resp and resp[0] else 0
            if uidvalidity and validity and validity != uidvalidity:
                last_uid = 0                         # Postfach neu nummeriert → wie erster Abruf
            if last_uid:
                typ, data = conn.uid("SEARCH", None, f"UID {last_uid + 1}:*")
            else:
                since = (datetime.now(timezone.utc) - timedelta(days=FIRST_SYNC_DAYS)).strftime("%d-%b-%Y")
                typ, data = conn.uid("SEARCH", None, "SINCE", since)
            uids = sorted(int(x) for x in (data[0] or b"").split() if int(x) > last_uid)[-MAX_FETCH:]
            out: list[FetchedMail] = []
            for uid in uids:
                typ, parts = conn.uid("FETCH", str(uid), "(RFC822.SIZE BODY.PEEK[])")
                raw = next((p[1] for p in parts or [] if isinstance(p, tuple) and len(p) > 1), None)
                if raw and len(raw) <= MAX_MAIL_BYTES:
                    out.append(FetchedMail(uid, raw))
                elif raw:
                    out.append(FetchedMail(uid, _too_big_stub(raw)))
            return validity, out
        except MailError:
            raise
        except (OSError, imaplib.IMAP4.error) as exc:
            raise _friendly(exc, "Abruf") from None
        finally:
            try:
                conn.logout()
            except Exception:  # noqa: BLE001
                pass


def _too_big_stub(raw: bytes) -> bytes:
    head = raw.split(b"\r\n\r\n", 1)[0]
    return head + b"\r\n\r\n(E-Mail zu gross fuer die Uebernahme - bitte direkt beim Anbieter ansehen)"


transport: Transport = Transport()


# =========================================================================== Mails bauen / lesen
def new_message_id(account_email: str) -> str:
    domain = account_email.rsplit("@", 1)[-1] or "schulmanager.local"
    return f"<sm.{int(time.time())}.{secrets.token_hex(8)}@{domain}>"


def build_mail(c: Creds, *, to: list[tuple[str, str]], cc: list[tuple[str, str]], subject: str, text: str,
               message_id: str, in_reply_to: Optional[str] = None, references: list[str] = (),
               attachments: list[tuple[str, str, bytes]] = ()) -> EmailMessage:
    """``to``/``cc`` = ``[(Name, Adresse)]``; BCC-Adressen stehen nicht im Kopf (nur als Empfänger beim Versand)."""
    msg = EmailMessage()
    msg["From"] = email.utils.formataddr((c.display_name, c.email)) if c.display_name else c.email
    if to:
        msg["To"] = ", ".join(email.utils.formataddr(x) for x in to)
    if cc:
        msg["Cc"] = ", ".join(email.utils.formataddr(x) for x in cc)
    msg["Subject"] = subject or "(ohne Betreff)"
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = message_id
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    refs = [r for r in references if r]
    if refs:
        msg["References"] = " ".join(refs[-20:])
    msg["X-Mailer"] = "Schulmanager"
    msg.set_content(text or "")
    for name, ctype, data in attachments:
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(data, maintype=maintype or "application", subtype=subtype or "octet-stream",
                           filename=name)
    return msg


_TAG = re.compile(r"<[^>]+>")
_BLOCK = re.compile(r"(?i)<\s*(br|/p|/div|/li|/tr|/h[1-6])\b[^>]*>")
_DROP = re.compile(r"(?is)<\s*(script|style|head)\b.*?<\s*/\s*\1\s*>")


def html_to_text(markup: str) -> str:
    text = _DROP.sub("", markup)
    text = _BLOCK.sub("\n", text)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()


@dataclass
class ParsedMail:
    message_id: str
    in_reply_to: list[str]
    subject: str
    from_addr: str
    from_name: str
    to: list[tuple[str, str]]
    cc: list[tuple[str, str]]
    date: Optional[datetime]
    text: str
    attachments: list[tuple[str, str, bytes]] = field(default_factory=list)


def _addrs(values: list[str]) -> list[tuple[str, str]]:
    return [(n, a.lower()) for n, a in email.utils.getaddresses(values) if a and "@" in a]


def parse_mail(raw: bytes) -> ParsedMail:
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    frm = _addrs([str(msg.get("From", ""))])
    name, addr = frm[0] if frm else ("", "")
    refs = " ".join(str(msg.get(h, "")) for h in ("In-Reply-To", "References"))
    try:
        when = email.utils.parsedate_to_datetime(str(msg.get("Date"))) if msg.get("Date") else None
        if when is not None and when.tzinfo is not None:
            when = when.astimezone(timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError):
        when = None
    text = ""
    body = msg.get_body(preferencelist=("plain", "html")) if msg.is_multipart() or msg.get_content_type() in (
        "text/plain", "text/html") else None
    if body is not None:
        try:
            content = body.get_content()
        except (LookupError, ValueError):
            content = body.get_payload(decode=True).decode("utf-8", "replace") if body.get_payload(decode=True) else ""
        text = html_to_text(content) if body.get_content_type() == "text/html" else str(content)
    attachments = []
    for part in msg.iter_attachments() if msg.is_multipart() else []:
        data = part.get_payload(decode=True) or b""
        if not data or len(data) > MAX_ATTACHMENT_BYTES:
            continue
        attachments.append((part.get_filename() or "anhang", part.get_content_type(), data))
    return ParsedMail(
        message_id=str(msg.get("Message-ID", "")).strip()[:500],
        in_reply_to=re.findall(r"<[^<>\s]+>", refs),
        subject=str(msg.get("Subject", "")).strip(),
        from_addr=addr, from_name=name,
        to=_addrs([str(x) for x in msg.get_all("To", [])]),
        cc=_addrs([str(x) for x in msg.get_all("Cc", [])]),
        date=when, text=text.strip()[:MAX_BODY_CHARS], attachments=attachments[:10])


# =========================================================================== Hintergrund-Abruf
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_wake = threading.Event()
_lock = threading.Lock()
sync_hook: Optional[Callable[[], int]] = None      # wird von routes/features_mail gesetzt (sync_all)


def _loop() -> None:
    from .config import config
    interval = max(1.0, float(getattr(config, "mail_sync_minutes", 5) or 5)) * 60
    while not _stop.is_set():
        try:
            if sync_hook is not None:
                sync_hook()
        except Exception:  # noqa: BLE001 - nie den Thread verlieren
            log.exception("E-Mail-Abruf fehlgeschlagen")
        _wake.wait(interval)
        _wake.clear()


def start() -> bool:
    global _thread
    from .config import config
    if not getattr(config, "mail_sync", True):
        log.info("E-Mail-Abruf deaktiviert (SM_MAIL_SYNC=0)")
        return False
    with _lock:
        if _thread is not None and _thread.is_alive():
            return True
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="sm-mail", daemon=True)
        _thread.start()
    log.info("E-Mail-Abruf gestartet")
    return True


def stop() -> None:
    global _thread
    _stop.set()
    _wake.set()
    with _lock:
        t, _thread = _thread, None
    if t is not None and t.is_alive() and t is not threading.current_thread():
        t.join(5)


def kick() -> None:
    _wake.set()
