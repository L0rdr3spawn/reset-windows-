"""SMS-Versand (§11.2) – nur Standardbibliothek (``urllib``), Zustellung über die Outbox (Art ``sms``).

Anbieter (``SM_SMS_PROVIDER``):

* leer – aus (``auth_messages.sms_available()`` ist dann nur mit Test-Postausgang wahr),
* ``log`` – schreibt die SMS ins Server-Log (Entwicklung; in Produktion ohne Text),
* ``webhook`` – ``POST SM_SMS_URL`` mit JSON ``{"to": "+49…", "text": "…"}``, optional ``Authorization: Bearer
  SM_SMS_TOKEN``; jede 2xx-Antwort gilt als Erfolg,
* ``twilio`` – REST-API ``Accounts/<SM_SMS_ACCOUNT_SID>/Messages.json`` (Basic-Auth mit ``SM_SMS_TOKEN``,
  Absender ``SM_SMS_FROM``),
* ``seven`` – seven.io ``POST https://gateway.seven.io/api/sms`` (Header ``X-Api-Key: SM_SMS_TOKEN``, optional
  Absender ``SM_SMS_FROM``).

Fehler (Netz, Zeitlimit ``SM_SMS_TIMEOUT``, Nicht-2xx, Fehlercode des Anbieters) → :class:`SmsError`; der
Outbox-Dispatcher versucht es dann mit Backoff erneut.

Telefonnummern: :func:`normalize_phone` bringt deutsche und internationale Eingaben in E.164-Form
(``0171 1234567`` → ``+491711234567``), :func:`mask_phone` / :func:`format_phone` für die Anzeige.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from . import net_guard

log = logging.getLogger("schulmanager.sms")

PROVIDERS: tuple[str, ...] = ("log", "webhook", "twilio", "seven")
TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
SEVEN_URL = "https://gateway.seven.io/api/sms"
MAX_TEXT = 640  # 4 SMS-Teile – Codes/Hinweise sind deutlich kürzer
DEFAULT_COUNTRY = "49"


class SmsError(RuntimeError):
    """SMS konnte nicht zugestellt werden (Outbox versucht es erneut)."""


# =========================================================================== Nummern
_SEPARATORS = re.compile(r"[\s\-/.()   ]")
_TRUNK_ZERO = re.compile(r"\(\s*0\s*\)")


def normalize_phone(raw: str | None, default_country: str = DEFAULT_COUNTRY) -> str | None:
    """Telefonnummer → E.164 (``+491711234567``) oder ``None`` (ungültig).

    Erlaubt sind übliche Schreibweisen: ``0171 1234567``, ``0171/123 45 67``, ``+49 (0)171 1234567``,
    ``+49 (171) 1234567``, ``0049 171 1234567``, ``+43 664 1234567``. Eine Zahl ohne führende ``0``/``+``/``00``
    ist mehrdeutig und wird abgelehnt. Nummern mit Ländervorwahl ``+49`` verlieren eine fälschlich mitgeschriebene
    Verkehrsausscheidungsziffer (``+490171…`` → ``+49171…``).
    """
    if not raw:
        return None
    text = str(raw).strip()
    if not text or len(text) > 40:
        return None
    text = _TRUNK_ZERO.sub("", text)          # „+49 (0) 171 …“
    text = _SEPARATORS.sub("", text)
    if text.startswith("+"):
        digits = text[1:]
    elif text.startswith("00"):
        digits = text[2:]
    elif text.startswith("0"):
        digits = default_country + text[1:]
    else:
        return None
    if not digits.isdigit() or digits.startswith("0"):
        return None
    if digits.startswith("49") and digits[2:3] == "0":
        digits = "49" + digits[3:]
    # E.164: höchstens 15 Ziffern; mindestens Ländervorwahl + 6-stellige Teilnehmernummer
    if not 8 <= len(digits) <= 15:
        return None
    if digits.startswith("49") and not 9 <= len(digits) <= 15:
        return None
    return "+" + digits


def looks_like_phone(value: str | None) -> bool:
    """Eingabe besteht nur aus Ziffern, ``+`` und Trennzeichen (für die Kennungs-Erkennung)."""
    if not value:
        return False
    stripped = _SEPARATORS.sub("", value.strip())
    return bool(stripped) and bool(re.fullmatch(r"\+?\d{6,20}", stripped))


def format_phone(e164: str | None) -> str:
    """Lesbare Form für Admins: ``+49 171 1234567`` (deutsche Mobil-/Ortsnummern grob gegliedert)."""
    if not e164 or not e164.startswith("+"):
        return e164 or ""
    digits = e164[1:]
    if digits.startswith("49"):
        rest = digits[2:]
        return f"+49 {rest[:3]} {rest[3:]}".strip()
    return f"+{digits[:2]} {digits[2:]}"


def mask_phone(e164: str | None) -> str:
    """Maskierte Anzeige: ``+49 171 •••••67`` (Ländervorwahl, Vorwahl-Anfang, letzte zwei Ziffern)."""
    if not e164 or not e164.startswith("+") or len(e164) < 6:
        return "•••"
    digits = e164[1:]
    cc, rest = (digits[:2], digits[2:])
    head = rest[:3]
    tail = rest[-2:]
    hidden = max(1, len(rest) - len(head) - len(tail))
    return f"+{cc} {head} {'•' * hidden}{tail}"


def phone_hash(e164: str) -> str:
    """HMAC der E.164-Nummer (Suche nach Nummer, ohne sie im Klartext zu speichern)."""
    from .config import config

    return hmac.new(config.secret_key.encode(), f"phone:{e164}".encode(), hashlib.sha256).hexdigest()


# =========================================================================== Versand
def configured() -> bool:
    """Ein (vollständig konfigurierter) Anbieter ist eingestellt."""
    from .config import config

    return config.sms_provider in PROVIDERS


def send_sms(to: str, text: str) -> None:
    """Stellt eine SMS über den eingestellten Anbieter zu (wirft :class:`SmsError`)."""
    from .config import config

    number = normalize_phone(to)
    if number is None:
        raise SmsError("Ungültige Telefonnummer")
    text = (text or "").strip()[:MAX_TEXT]
    if not text:
        raise SmsError("Leere SMS")
    provider = config.sms_provider
    if provider == "log":
        if config.is_production:
            log.info("SMS an %s (%d Zeichen, Text ausgeblendet)", mask_phone(number), len(text))
        else:
            log.info("SMS an %s: %s", mask_phone(number), text)
        return
    if provider == "webhook":
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if config.sms_token:
            headers["Authorization"] = f"Bearer {config.sms_token}"
        body = json.dumps({"to": number, "text": text}, ensure_ascii=False).encode("utf-8")
        _post(config.sms_url or "", body, headers)
        return
    if provider == "twilio":
        sid = config.sms_account_sid or ""
        auth = base64.b64encode(f"{sid}:{config.sms_token or ''}".encode()).decode("ascii")
        form = urllib.parse.urlencode({"To": number, "From": config.sms_from or "", "Body": text}).encode()
        _post(TWILIO_URL.format(sid=urllib.parse.quote(sid, safe="")), form,
              {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
        return
    if provider == "seven":
        params = {"to": number, "text": text, "json": "1"}
        if config.sms_from:
            params["from"] = config.sms_from
        raw = _post(SEVEN_URL, urllib.parse.urlencode(params).encode(),
                    {"X-Api-Key": config.sms_token or "", "Content-Type": "application/x-www-form-urlencoded",
                     "Accept": "application/json"})
        _check_seven(raw)
        return
    raise SmsError("Kein SMS-Anbieter eingerichtet (SM_SMS_PROVIDER)")


def _post(url: str, body: bytes, headers: dict[str, str]) -> bytes:
    from .config import config

    if not url.startswith(("https://", "http://")):
        raise SmsError("Ungültige Adresse des SMS-Anbieters")
    req = urllib.request.Request(url, data=body, headers={"User-Agent": "Schulmanager-SMS/1", **headers},
                                 method="POST")
    try:
        with net_guard.urlopen(req, "sms", timeout=config.sms_timeout) as resp:  # Adresse vom Admin, geprüft
            data = resp.read(65536)
            if not 200 <= resp.status < 300:
                raise SmsError(f"HTTP {resp.status}")
            return data
    except urllib.error.HTTPError as exc:
        raise SmsError(f"HTTP {exc.code}") from None
    except net_guard.BlockedTarget:
        raise SmsError("Die Adresse des SMS-Anbieters ist nicht zulässig (SM_OUTBOUND_ALLOW)") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if isinstance(getattr(exc, "reason", None), net_guard.BlockedTarget):
            raise SmsError("Die Adresse des SMS-Anbieters ist nicht zulässig (SM_OUTBOUND_ALLOW)") from None
        raise SmsError(f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}") from None


def _check_seven(raw: bytes) -> None:
    """seven.io antwortet mit Code ``100`` (Erfolg) – als JSON ``{"success": "100", …}`` oder als Text."""
    text = raw.decode("utf-8", "replace").strip()
    code = text
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            code = str(data.get("success", ""))
        elif isinstance(data, (int, str)):
            code = str(data)
    except json.JSONDecodeError:
        code = text.splitlines()[0] if text else ""
    if code.strip() != "100":
        raise SmsError(f"seven.io meldet Fehlercode {code.strip()[:20] or '?'}")
