"""Kryptografische Grundbausteine (nur Standardbibliothek).

* Passwort-Hashing mit ``hashlib.scrypt``: Format ``scrypt$<n>$<r>$<p>$<salt_b64>$<hash_b64>``
  (Parameter im Hash → spätere Erhöhung möglich, :func:`needs_rehash`), Vergleich in konstanter Zeit.
* Passwortregeln: Personal/Eltern ≥ 10 Zeichen, Schüler ≥ 8.
* Gut lesbare Startpasswörter (:func:`generate_password`).
* Zufallstoken + HMAC-Hash zum Speichern (Sitzungen, API-Tokens).
* TOTP (RFC 6238, SHA-1, 30 s, 6 Stellen, ±1 Zeitfenster).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import threading
import time
import unicodedata
from urllib.parse import quote, urlencode

from .config import config

# --------------------------------------------------------------------------- Passwörter
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32
TEMP_PASSWORD_N = 2 ** 11  # Startpasswörter sind zufällig (≈ 60 Bit) → günstigere Parameter genügen


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int, dklen: int = _DKLEN) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p,
                          maxmem=max(64 * 1024 * 1024, 2 * 128 * n * r * p), dklen=dklen)


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii").rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s + "=" * (-len(s) % 4))


def hash_password(password: str, n: int | None = None) -> str:
    """Erzeugt einen scrypt-Hash mit zufälligem Salt."""
    n = n or config.scrypt_n
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, n, _SCRYPT_R, _SCRYPT_P)
    return f"scrypt${n}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str | None) -> bool:
    """Prüft ``password`` gegen ``stored`` (konstante Vergleichszeit, auch bei leerem Hash)."""
    if not stored:
        _dummy_verify(password)
        return False
    try:
        algo, n_s, r_s, p_s, salt_s, hash_s = stored.split("$")
        if algo != "scrypt":
            return False
        expected = _unb64(hash_s)
        digest = _scrypt(password, _unb64(salt_s), int(n_s), int(r_s), int(p_s), len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)


_dummy_hash: str | None = None
_dummy_lock = threading.Lock()


def _dummy_verify(password: str) -> None:
    """Verbraucht dieselbe Zeit wie eine echte Prüfung (gegen Benutzernamen-Enumeration)."""
    global _dummy_hash
    with _dummy_lock:
        if _dummy_hash is None or f"${config.scrypt_n}$" not in _dummy_hash:
            _dummy_hash = hash_password(secrets.token_urlsafe(12))
    verify_password(password, _dummy_hash)


def needs_rehash(stored: str | None) -> bool:
    """``True``, wenn der Hash schwächere Parameter als die aktuelle Konfiguration nutzt."""
    if not stored:
        return False
    try:
        algo, n_s, *_ = stored.split("$")
        return algo != "scrypt" or int(n_s) < config.scrypt_n
    except ValueError:
        return True


MIN_LENGTH_DEFAULT = 10
MIN_LENGTH = {"schueler": 8}
MAX_LENGTH = 256
_COMMON = {"passwort", "password", "passwort123", "password123", "1234567890", "12345678", "123456789",
           "qwertzuiop", "qwertyuiop", "schulmanager", "schule1234", "abcdefghij", "0987654321",
           "hallo12345", "iloveyou", "11111111", "1111111111", "admin12345", "letmein123"}


def min_length(role: str) -> int:
    return MIN_LENGTH.get(role, MIN_LENGTH_DEFAULT)


def password_problems(password: str, role: str, username: str = "") -> list[str]:
    """Liste der verletzten Passwortregeln (leer = in Ordnung). Deutsche Meldungen."""
    problems = []
    n = min_length(role)
    if len(password) < n:
        problems.append(f"Das Passwort muss mindestens {n} Zeichen lang sein.")
    if len(password) > MAX_LENGTH:
        problems.append(f"Das Passwort darf höchstens {MAX_LENGTH} Zeichen lang sein.")
    low = password.lower()
    if low in _COMMON or len(set(password)) < 4:
        problems.append("Das Passwort ist zu leicht zu erraten.")
    if username and len(username) >= 3 and username.lower() in low:
        problems.append("Das Passwort darf den Benutzernamen nicht enthalten.")
    return problems


_PW_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # ohne 0/o/1/l/i


def generate_password(groups: int = 3, size: int = 4) -> str:
    """Gut lesbares Zufallspasswort, z. B. ``kd7m-p4vx-h9tq`` (≈ 59 Bit)."""
    return "-".join("".join(secrets.choice(_PW_ALPHABET) for _ in range(size)) for _ in range(groups))


# --------------------------------------------------------------------------- Tokens
def new_token(nbytes: int = 32) -> str:
    """Kryptografisch zufälliges URL-sicheres Token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """HMAC-SHA256(secret_key, token) als Hex – so werden Sitzungs-/API-Tokens gespeichert."""
    return hmac.new(config.secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()


def totp_aad(user_id: int) -> str:
    return f"users.totp_secret:{user_id}"


def get_totp_secret(user) -> str | None:
    """TOTP-Geheimnis eines Kontos im Klartext (in der DB liegt es verschlüsselt in ``totp_secret_enc``, S-09).
    Altbestand im Klartext-Feld ``totp_secret`` (vor Migration 0045) wird weiter gelesen."""
    from . import crypto

    raw = getattr(user, "totp_secret_enc", None)
    if raw:
        try:
            return crypto.decrypt_text(raw, totp_aad(user.id))
        except crypto.CryptoError:
            return None
    return user.totp_secret or None


def set_totp_secret(user, secret: str | None) -> None:
    """Legt das TOTP-Geheimnis verschlüsselt ab (``None`` = löschen); das alte Klartext-Feld wird geleert."""
    from . import crypto

    user.totp_secret = None
    user.totp_secret_enc = crypto.encrypt_text(secret, totp_aad(user.id)) if secret else None


def constant_equals(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return hmac.compare_digest(a.encode(), b.encode())


# --------------------------------------------------------------------------- TOTP (RFC 6238)
TOTP_PERIOD = 30
TOTP_DIGITS = 6


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _hotp(secret: str, counter: int, digits: int = TOTP_DIGITS) -> str:
    key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    code = (struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def totp_now(secret: str, at: float | None = None) -> str:
    """Aktueller TOTP-Code (für Tests/Einrichtung)."""
    return _hotp(secret, int((time.time() if at is None else at) // TOTP_PERIOD))


_used_steps: dict[tuple[str, int], float] = {}
_used_lock = threading.Lock()


def verify_totp(secret: str | None, code: str | None, at: float | None = None, window: int = 1,
                replay_key: str | None = None) -> bool:
    """Prüft einen TOTP-Code mit ±``window`` Zeitfenstern.

    Mit ``replay_key`` (z. B. Benutzer-ID) wird ein bereits verwendeter Code
    innerhalb seines Gültigkeitsfensters abgelehnt (prozesslokal).
    """
    if not secret or not code:
        return False
    code = "".join(ch for ch in str(code) if ch.isdigit())
    if len(code) != TOTP_DIGITS:
        return False
    now = time.time() if at is None else at
    step = int(now // TOTP_PERIOD)
    for delta in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret, step + delta), code):
            if replay_key is not None:
                with _used_lock:
                    for k in [k for k, exp in _used_steps.items() if exp < now]:
                        _used_steps.pop(k, None)
                    # Geheimnis mit einbeziehen: neu eingerichtete 2FA (neues Secret) kollidiert nicht
                    fp = hashlib.sha256(secret.encode()).hexdigest()[:16]
                    key = (f"{replay_key}:{fp}", step + delta)
                    if key in _used_steps:
                        return False
                    _used_steps[key] = now + (window + 2) * TOTP_PERIOD
            return True
    return False


def otpauth_url(secret: str, username: str, issuer: str | None = None) -> str:
    """``otpauth://totp/…``-URL für Authenticator-Apps (QR-Code im Frontend)."""
    issuer = issuer or config.app_name
    label = quote(f"{issuer}:{username}")
    params = urlencode({"secret": secret, "issuer": issuer, "algorithm": "SHA1",
                        "digits": TOTP_DIGITS, "period": TOTP_PERIOD})
    return f"otpauth://totp/{label}?{params}"


# --------------------------------------------------------------------------- Benutzernamen
_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue", "ẞ": "ss"}


def ascii_slug(text: str, keep: str = "-") -> str:
    """ASCII-Normalisierung für Benutzernamen: ä→ae, ß→ss, Akzente entfernt, Kleinbuchstaben.

    Leerzeichen werden zu ``-``; erlaubt bleiben ``a-z0-9`` und Zeichen aus ``keep``.
    """
    out = "".join(_UMLAUTS.get(ch, ch) for ch in text.strip())
    out = unicodedata.normalize("NFKD", out).encode("ascii", "ignore").decode("ascii").lower()
    out = "-".join(out.split())
    out = "".join(ch for ch in out if ch.isalnum() or ch in keep)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-.")
