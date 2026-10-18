"""Umschlagverschlüsselung (Envelope Encryption) mit AES-256-GCM.

Jedes verschlüsselte Objekt bekommt einen eigenen, zufälligen 256-bit-Datenschlüssel (DEK). Der DEK wird mit dem
aktiven Master-Schlüssel (KEK) aus ``SM_ENCRYPTION_KEYS`` verschlüsselt („gewrappt“) und zusammen mit dem Chiffrat im
Token abgelegt. Eine Schlüsselrotation (:func:`rewrap`) tauscht nur den gewrappten DEK aus – die Nutzdaten bleiben
unverändert, deshalb ist sie auch bei vielen Objekten schnell.

Schlüsselring (``SM_ENCRYPTION_KEYS``)::

    SM_ENCRYPTION_KEYS="k2:<base64 32 Byte>,k1:<base64 32 Byte>"     # erster Eintrag = aktiv

* Produktion: Pflicht (``config.validate`` bricht sonst den Start ab).
* Entwicklung ohne Variable: Schlüssel ``dev`` wird per HKDF-SHA256 aus ``SM_SECRET_KEY`` abgeleitet (Warnung im Log).
  Ist die Variable gesetzt, bleibt ``dev`` als reiner Entschlüsselungs-Fallback im Ring (Umstieg ohne Datenverlust).
* Neuer Schlüssel: ``python -m schulmanager.server.cli gen-key``; Rotation: neuen Schlüssel VORN eintragen, Neustart,
  ``python -m schulmanager.server.cli rotate-keys``; den alten Schlüssel erst entfernen, wenn auch alle Sicherungen,
  die ihn noch brauchen, abgelaufen sind.

Formate (Zahlen big-endian)
---------------------------
``SM1`` – einzelnes Objekt (:func:`encrypt`/:func:`decrypt`)::

    b"SM1" | kid_len:u8 | kid | wrap_nonce:12 | wrapped_dek:48 | nonce:12 | ciphertext + tag:16
    wrapped_dek = AES-256-GCM(KEK[kid], wrap_nonce, DEK, aad = b"SM1|dek|" + kid)
    ciphertext  = AES-256-GCM(DEK, nonce, klartext, aad = b"SM1|data|" + aad)

Text-Token (:func:`encrypt_text`): ``"SM1." + base64url(binär, ohne "=")`` – reines ASCII, für ``Text``-Spalten.

``SMS1`` – Datei-Stream (blockweise, konstanter Speicherbedarf; :class:`StreamEncryptor`/:class:`StreamDecryptor`)::

    Kopf:   b"SMS1" | kid_len:u8 | kid | wrap_nonce:12 | wrapped_dek:48 | nonce_prefix:7 | chunk_size:u32
    Block:  AES-256-GCM(DEK, nonce_prefix | zähler:u32 | letzter:u8, block, aad = b"SMS1|" + chunk_size:u32 + aad)

(STREAM-Konstruktion: der Zähler verhindert Vertauschen/Weglassen von Blöcken, das Schluss-Flag Abschneiden und
Anhängen.) Alle Nonces sind zufällig (96 bit bzw. 56-bit-Präfix je Datei). Manipulation, falsches AAD oder ein
falscher Schlüssel führen zu :class:`InvalidToken`; eine unbekannte Schlüssel-ID zu :class:`UnknownKeyError`.

Weitere Features registrieren ihre verschlüsselten Spalten für ``cli rotate-keys`` mit
``register_rewrap("tabelle.spalte", fn)``; ``fn(db) -> int`` (Anzahl geänderter Zeilen), z. B. über :func:`rewrap_column`.
"""
from __future__ import annotations

import base64
import binascii
import logging
import os
import re
import secrets
import struct
import threading
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .config import ConfigError, config

log = logging.getLogger("schulmanager.crypto")

MAGIC = b"SM1"
STREAM_MAGIC = b"SMS1"
TEXT_PREFIX = "SM1."
KEY_BYTES = 32
NONCE_BYTES = 12
TAG_BYTES = 16
WRAPPED_BYTES = KEY_BYTES + TAG_BYTES
STREAM_PREFIX_BYTES = 7
DEFAULT_CHUNK_SIZE = 64 * 1024
MAX_CHUNK_SIZE = 16 * 1024 * 1024
DEV_KEY_ID = "dev"
KID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


class CryptoError(ValueError):
    """Basisklasse aller Verschlüsselungsfehler."""


class InvalidToken(CryptoError):
    """Token beschädigt, manipuliert, falsches AAD oder falscher Schlüssel."""


class UnknownKeyError(CryptoError):
    """Die Schlüssel-ID des Tokens ist nicht (mehr) im Schlüsselring ``SM_ENCRYPTION_KEYS``."""


# --------------------------------------------------------------------------- Schlüsselring
class KeyRing:
    """Master-Schlüssel (``kid`` → 32 Byte); ``active`` verschlüsselt neue Daten."""

    def __init__(self, keys: list[tuple[str, bytes]], *, derived: bool = False,
                 fallback: tuple[str, bytes] | None = None) -> None:
        if not keys:
            raise ConfigError("Schlüsselring ist leer")
        self.active: str = keys[0][0]
        self.derived = derived
        self._keys: dict[str, bytes] = dict(keys)
        if fallback is not None and fallback[0] not in self._keys:
            self._keys[fallback[0]] = fallback[1]
        self._aead: dict[str, AESGCM] = {kid: AESGCM(key) for kid, key in self._keys.items()}

    @property
    def key_ids(self) -> list[str]:
        return list(self._keys)

    def aead(self, kid: str) -> AESGCM:
        try:
            return self._aead[kid]
        except KeyError:
            raise UnknownKeyError(f"Schlüssel {kid!r} ist nicht in SM_ENCRYPTION_KEYS – ohne ihn sind diese Daten "
                                  "nicht lesbar") from None

    def fingerprint(self, kid: str) -> str:
        """Kurzer, nicht umkehrbarer Fingerabdruck eines Schlüssels (zum Abgleich ohne Offenlegung)."""
        digest = hashes.Hash(hashes.SHA256())
        digest.update(b"schulmanager/key-fingerprint|" + self._keys[kid])
        return digest.finalize().hex()[:12]


def _b64decode(value: str) -> bytes:
    value = value.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(value + "=" * (-len(value) % 4), validate=True)


def parse_keys(spec: str) -> list[tuple[str, bytes]]:
    """``"kid:base64,kid2:base64"`` → ``[(kid, key32), …]`` (erster = aktiv). Fehler → :class:`ConfigError`.

    Erlaubte Trenner zwischen Einträgen: Komma, Semikolon, Leerzeichen, Zeilenumbruch. Base64 normal oder URL-sicher.
    Fehlermeldungen enthalten nie Schlüsselmaterial.
    """
    entries = [e for e in re.split(r"[,;\s]+", spec or "") if e]
    if not entries:
        raise ConfigError("SM_ENCRYPTION_KEYS ist leer")
    out: list[tuple[str, bytes]] = []
    for n, entry in enumerate(entries, 1):
        kid, sep, material = entry.partition(":")
        if not sep or not KID_RE.match(kid):
            raise ConfigError(f"SM_ENCRYPTION_KEYS: Eintrag {n} hat nicht das Format 'id:base64' "
                              "(id: 1–32 Zeichen A-Z a-z 0-9 _ -)")
        try:
            key = _b64decode(material)
        except (binascii.Error, ValueError):
            raise ConfigError(f"SM_ENCRYPTION_KEYS: Schlüssel {kid!r} ist kein gültiges Base64") from None
        if len(key) != KEY_BYTES:
            raise ConfigError(f"SM_ENCRYPTION_KEYS: Schlüssel {kid!r} muss genau 32 Byte lang sein "
                              f"(ist {len(key)} Byte) – neu erzeugen mit `cli gen-key`")
        if any(k == kid for k, _ in out):
            raise ConfigError(f"SM_ENCRYPTION_KEYS: Schlüssel-ID {kid!r} ist doppelt")
        out.append((kid, key))
    return out


def derive_dev_key(secret: str) -> bytes:
    """Entwicklungsschlüssel aus ``SM_SECRET_KEY`` (HKDF-SHA256) – nie in Produktion verwenden."""
    return HKDF(algorithm=hashes.SHA256(), length=KEY_BYTES, salt=b"schulmanager/envelope-encryption",
                info=b"SM_ENCRYPTION_KEYS/dev/v1").derive(secret.encode("utf-8"))


def generate_key(kid: str | None = None) -> str:
    """Neuer Eintrag für ``SM_ENCRYPTION_KEYS``: ``"<kid>:<base64 32 Byte>"`` (kid Standard: ``kJJJJMMTT``)."""
    kid = kid or "k" + datetime.now(timezone.utc).strftime("%Y%m%d")
    if not KID_RE.match(kid) or kid == DEV_KEY_ID:
        raise ValueError("Schlüssel-ID: 1–32 Zeichen A-Z a-z 0-9 _ - (nicht 'dev')")
    return f"{kid}:{base64.b64encode(secrets.token_bytes(KEY_BYTES)).decode('ascii')}"


_lock = threading.Lock()
_cache: tuple[tuple[Any, ...], KeyRing] | None = None
_warned_dev = False


def keyring() -> KeyRing:
    """Aktueller Schlüsselring (aus ``config``; wird bei geänderter Konfiguration neu aufgebaut)."""
    global _cache, _warned_dev
    spec = (config.encryption_keys or "").strip()
    production = config.is_production
    secret = "" if production else config.secret_key
    cache_key = (spec, production, secret)
    cached = _cache
    if cached is not None and cached[0] == cache_key:
        return cached[1]
    with _lock:
        if _cache is not None and _cache[0] == cache_key:
            return _cache[1]
        if spec:
            fallback = None if production else (DEV_KEY_ID, derive_dev_key(secret))
            ring = KeyRing(parse_keys(spec), fallback=fallback)
        elif production:
            raise ConfigError("SM_ENCRYPTION_KEYS muss in Produktion gesetzt sein "
                              "(erzeugen: python -m schulmanager.server.cli gen-key)")
        else:
            if not _warned_dev:
                log.warning("SM_ENCRYPTION_KEYS ist nicht gesetzt – Entwicklungsschlüssel wird aus SM_SECRET_KEY "
                            "abgeleitet (NICHT für Produktion; Daten sind nach Änderung von SM_SECRET_KEY unlesbar)")
                _warned_dev = True
            ring = KeyRing([(DEV_KEY_ID, derive_dev_key(secret))], derived=True)
        _cache = (cache_key, ring)
        return ring


def reset() -> None:
    """Verwirft den zwischengespeicherten Schlüsselring (Tests)."""
    global _cache, _warned_dev
    with _lock:
        _cache = None
        _warned_dev = False


def active_key_id() -> str:
    """ID des Schlüssels, mit dem neue Daten verschlüsselt werden."""
    return keyring().active


def describe() -> dict[str, Any]:
    """Status ohne Schlüsselmaterial (für Systemansicht/CLI)."""
    ring = keyring()
    return {"active": ring.active, "key_ids": ring.key_ids, "source": "derived" if ring.derived else "env",
            "fingerprints": {kid: ring.fingerprint(kid) for kid in ring.key_ids}}


# --------------------------------------------------------------------------- Hilfen
def _as_bytes(value: bytes | bytearray | memoryview | str, what: str = "aad") -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    raise TypeError(f"{what} muss bytes oder str sein")


def _wrap(ring: KeyRing, magic: bytes, kid: str, dek: bytes) -> bytes:
    kid_b = kid.encode("ascii")
    nonce = os.urandom(NONCE_BYTES)
    wrapped = ring.aead(kid).encrypt(nonce, dek, magic + b"|dek|" + kid_b)
    return magic + bytes([len(kid_b)]) + kid_b + nonce + wrapped


def _parse_header(token: bytes, magic: bytes) -> tuple[str, bytes, bytes, int]:
    """→ (kid, wrap_nonce, wrapped_dek, offset hinter dem Kopf)."""
    if token[:len(magic)] != magic:
        raise InvalidToken("Kein gültiges Token (Kennung fehlt)")
    pos = len(magic)
    if len(token) < pos + 1:
        raise InvalidToken("Token ist zu kurz")
    kid_len = token[pos]
    pos += 1
    end = pos + kid_len + NONCE_BYTES + WRAPPED_BYTES
    if kid_len == 0 or len(token) < end:
        raise InvalidToken("Token ist zu kurz")
    try:
        kid = token[pos:pos + kid_len].decode("ascii")
    except UnicodeDecodeError:
        raise InvalidToken("Ungültige Schlüssel-ID im Token") from None
    if not KID_RE.match(kid):
        raise InvalidToken("Ungültige Schlüssel-ID im Token")
    pos += kid_len
    return kid, token[pos:pos + NONCE_BYTES], token[pos + NONCE_BYTES:end], end


def _unwrap(ring: KeyRing, magic: bytes, kid: str, nonce: bytes, wrapped: bytes) -> bytes:
    try:
        return ring.aead(kid).decrypt(nonce, wrapped, magic + b"|dek|" + kid.encode("ascii"))
    except InvalidTag:
        raise InvalidToken("Datenschlüssel lässt sich nicht entschlüsseln (Token manipuliert oder falscher "
                           "Master-Schlüssel)") from None


# --------------------------------------------------------------------------- einzelne Objekte (SM1)
def encrypt(data: bytes, aad: bytes = b"") -> bytes:
    """Verschlüsselt ``data`` mit eigenem Datenschlüssel → binäres ``SM1``-Token.

    ``aad`` (zusätzliche authentifizierte Daten, z. B. ``b"messages.body:42"``) wird nicht gespeichert, muss beim
    Entschlüsseln aber identisch angegeben werden – so lässt sich ein Token nicht in eine andere Zeile verschieben.
    """
    ring = keyring()
    dek = os.urandom(KEY_BYTES)
    header = _wrap(ring, MAGIC, ring.active, dek)
    nonce = os.urandom(NONCE_BYTES)
    ciphertext = AESGCM(dek).encrypt(nonce, _as_bytes(data, "data"), b"SM1|data|" + _as_bytes(aad))
    return header + nonce + ciphertext


def decrypt(token: bytes, aad: bytes = b"") -> bytes:
    """Entschlüsselt ein ``SM1``-Token; :class:`InvalidToken` bei Manipulation/falschem AAD."""
    raw = _as_bytes(token, "token") if not isinstance(token, str) else _text_to_bytes(token)
    kid, wrap_nonce, wrapped, pos = _parse_header(raw, MAGIC)
    ring = keyring()
    dek = _unwrap(ring, MAGIC, kid, wrap_nonce, wrapped)
    if len(raw) < pos + NONCE_BYTES + TAG_BYTES:
        raise InvalidToken("Token ist zu kurz")
    nonce, ciphertext = raw[pos:pos + NONCE_BYTES], raw[pos + NONCE_BYTES:]
    try:
        return AESGCM(dek).decrypt(nonce, ciphertext, b"SM1|data|" + _as_bytes(aad))
    except InvalidTag:
        raise InvalidToken("Entschlüsselung fehlgeschlagen (Daten manipuliert oder falsches AAD)") from None


def _text_to_bytes(token: str) -> bytes:
    if not isinstance(token, str) or not token.startswith(TEXT_PREFIX):
        raise InvalidToken("Kein gültiges Text-Token (Präfix 'SM1.' fehlt)")
    body = token[len(TEXT_PREFIX):]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", body):
        raise InvalidToken("Text-Token enthält ungültige Zeichen")
    try:
        return base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    except (binascii.Error, ValueError):
        raise InvalidToken("Text-Token ist kein gültiges Base64") from None


def _bytes_to_text(raw: bytes) -> str:
    return TEXT_PREFIX + base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def encrypt_text(text: str, aad: str = "") -> str:
    """Verschlüsselt Text → ASCII-Token ``"SM1.…"`` (für ``Text``-Spalten)."""
    if not isinstance(text, str):
        raise TypeError("text muss str sein")
    return _bytes_to_text(encrypt(text.encode("utf-8"), _as_bytes(aad)))


def decrypt_text(token: str, aad: str = "") -> str:
    """Gegenstück zu :func:`encrypt_text`."""
    data = decrypt(_text_to_bytes(token), _as_bytes(aad))
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise InvalidToken("Entschlüsselter Inhalt ist kein UTF-8-Text") from None


def is_token(value: Any) -> bool:
    """Sieht ``value`` wie ein Token dieses Moduls aus (``SM1.``-Text, ``SM1``/``SMS1``-Binär)?"""
    if isinstance(value, str):
        return value.startswith(TEXT_PREFIX)
    if isinstance(value, (bytes, bytearray, memoryview)):
        head = bytes(value[:4])
        return head.startswith(MAGIC) or head == STREAM_MAGIC
    return False


def key_id_of(token: bytes | str) -> str:
    """Schlüssel-ID eines Tokens (Text, ``SM1`` oder ``SMS1``-Kopf) – ohne zu entschlüsseln."""
    raw = _text_to_bytes(token) if isinstance(token, str) else _as_bytes(token, "token")
    magic = STREAM_MAGIC if raw[:4] == STREAM_MAGIC else MAGIC
    return _parse_header(raw, magic)[0]


def rewrap(token: bytes | str) -> bytes | str:
    """Schlüsselrotation: wrappt den Datenschlüssel mit dem aktiven Master-Schlüssel neu.

    Gibt das Token unverändert zurück, wenn es schon den aktiven Schlüssel nutzt. Der Typ bleibt erhalten
    (Text → Text, Bytes → Bytes). Die Nutzdaten (und damit das AAD) werden nicht angefasst.
    """
    if isinstance(token, str):
        raw = _text_to_bytes(token)
        new = rewrap(raw)
        return token if new is raw else _bytes_to_text(new)  # type: ignore[arg-type]
    raw = _as_bytes(token, "token")
    magic = STREAM_MAGIC if raw[:4] == STREAM_MAGIC else MAGIC
    kid, wrap_nonce, wrapped, pos = _parse_header(raw, magic)
    ring = keyring()
    if kid == ring.active:
        return token if isinstance(token, bytes) else raw
    dek = _unwrap(ring, magic, kid, wrap_nonce, wrapped)
    return _wrap(ring, magic, ring.active, dek) + raw[pos:]


def needs_rewrap(token: bytes | str) -> bool:
    return key_id_of(token) != active_key_id()


def reencrypt(token: bytes | str, aad: bytes | str = b"") -> bytes | str:
    """Vollständige Neuverschlüsselung mit neuem Datenschlüssel (z. B. nach Kompromittierung eines Master-Schlüssels)."""
    if isinstance(token, str):
        return encrypt_text(decrypt_text(token, aad if isinstance(aad, str) else aad.decode("utf-8")),
                            aad if isinstance(aad, str) else aad.decode("utf-8"))
    return encrypt(decrypt(token, _as_bytes(aad)), _as_bytes(aad))


# --------------------------------------------------------------------------- Datei-Streams (SMS1)
def _stream_aad(chunk_size: int, aad: bytes) -> bytes:
    return b"SMS1|" + struct.pack(">I", chunk_size) + aad


def _stream_nonce(prefix: bytes, counter: int, last: bool) -> bytes:
    if counter >= 2 ** 32:
        raise CryptoError("Datei zu groß für das Stream-Format")
    return prefix + struct.pack(">IB", counter, 1 if last else 0)


class StreamEncryptor:
    """Blockweise Verschlüsselung (``SMS1``). ``header`` zuerst schreiben, dann ``update()``-Ausgaben, dann
    ``finalize()``. Speicherbedarf: ein Block (Standard 64 KiB)."""

    def __init__(self, aad: bytes | str = b"", chunk_size: int = DEFAULT_CHUNK_SIZE) -> None:
        if not 1024 <= chunk_size <= MAX_CHUNK_SIZE:
            raise ValueError("chunk_size außerhalb 1 KiB … 16 MiB")
        ring = keyring()
        dek = os.urandom(KEY_BYTES)
        self.key_id = ring.active
        self.chunk_size = chunk_size
        self._prefix = os.urandom(STREAM_PREFIX_BYTES)
        self.header = (_wrap(ring, STREAM_MAGIC, ring.active, dek) + self._prefix
                       + struct.pack(">I", chunk_size))
        self._aead = AESGCM(dek)
        self._aad = _stream_aad(chunk_size, _as_bytes(aad))
        self._buf = bytearray()
        self._counter = 0
        self._done = False

    def _seal(self, block: bytes, last: bool) -> bytes:
        out = self._aead.encrypt(_stream_nonce(self._prefix, self._counter, last), block, self._aad)
        self._counter += 1
        return out

    def update(self, data: bytes | bytearray | memoryview) -> bytes:
        if self._done:
            raise CryptoError("Stream bereits abgeschlossen")
        self._buf += data
        out = []
        size = self.chunk_size
        # Mindestens einen Block zurückhalten: erst finalize() weiß, welcher der letzte ist.
        while len(self._buf) > size:
            out.append(self._seal(bytes(self._buf[:size]), False))
            del self._buf[:size]
        return b"".join(out)

    def finalize(self) -> bytes:
        if self._done:
            raise CryptoError("Stream bereits abgeschlossen")
        self._done = True
        last = self._seal(bytes(self._buf), True)
        self._buf.clear()
        return last


def stream_header_length(prefix: bytes) -> int:
    """Länge des ``SMS1``-Kopfs (benötigt die ersten 5 Byte)."""
    if len(prefix) < 5 or prefix[:4] != STREAM_MAGIC:
        raise InvalidToken("Keine verschlüsselte Datei (Kennung SMS1 fehlt)")
    return 4 + 1 + prefix[4] + NONCE_BYTES + WRAPPED_BYTES + STREAM_PREFIX_BYTES + 4


class StreamDecryptor:
    """Gegenstück zu :class:`StreamEncryptor`; ``header`` = vollständiger Kopf (siehe :func:`stream_header_length`).

    ``update()`` gibt nur bereits geprüfte Blöcke aus; ``finalize()`` prüft den Schlussblock. Fehlt er (Datei
    abgeschnitten) oder wurde etwas verändert/angehängt, folgt :class:`InvalidToken`.
    """

    def __init__(self, header: bytes, aad: bytes | str = b"") -> None:
        kid, wrap_nonce, wrapped, pos = _parse_header(bytes(header), STREAM_MAGIC)
        if len(header) != pos + STREAM_PREFIX_BYTES + 4:
            raise InvalidToken("Dateikopf hat die falsche Länge")
        self.key_id = kid
        dek = _unwrap(keyring(), STREAM_MAGIC, kid, wrap_nonce, wrapped)
        self._prefix = bytes(header[pos:pos + STREAM_PREFIX_BYTES])
        (self.chunk_size,) = struct.unpack(">I", header[pos + STREAM_PREFIX_BYTES:pos + STREAM_PREFIX_BYTES + 4])
        if not 1024 <= self.chunk_size <= MAX_CHUNK_SIZE:
            raise InvalidToken("Ungültige Blockgröße im Dateikopf")
        self._aead = AESGCM(dek)
        self._aad = _stream_aad(self.chunk_size, _as_bytes(aad))
        self._buf = bytearray()
        self._counter = 0
        self._done = False

    def _open(self, block: bytes, last: bool) -> bytes:
        try:
            out = self._aead.decrypt(_stream_nonce(self._prefix, self._counter, last), block, self._aad)
        except InvalidTag:
            raise InvalidToken("Datei ist beschädigt oder manipuliert (Block "
                               f"{self._counter + 1} ungültig)") from None
        self._counter += 1
        return out

    def update(self, data: bytes | bytearray | memoryview) -> bytes:
        if self._done:
            raise InvalidToken("Daten hinter dem Dateiende")
        self._buf += data
        out = []
        size = self.chunk_size + TAG_BYTES
        while len(self._buf) > size:
            out.append(self._open(bytes(self._buf[:size]), False))
            del self._buf[:size]
        return b"".join(out)

    def finalize(self) -> bytes:
        if self._done:
            raise InvalidToken("Stream bereits abgeschlossen")
        self._done = True
        if len(self._buf) < TAG_BYTES:
            raise InvalidToken("Datei ist abgeschnitten (Schlussblock fehlt)")
        out = self._open(bytes(self._buf), True)
        self._buf.clear()
        return out


def read_stream_header(src: IO[bytes]) -> bytes:
    """Liest den ``SMS1``-Kopf aus einer geöffneten Datei."""
    first = src.read(5)
    total = stream_header_length(first)
    rest = src.read(total - 5)
    if len(rest) != total - 5:
        raise InvalidToken("Dateikopf ist abgeschnitten")
    return first + rest


def encrypt_stream(src: IO[bytes], dst: IO[bytes], aad: bytes | str = b"",
                   chunk_size: int = DEFAULT_CHUNK_SIZE) -> int:
    """``src`` (Klartext) → ``dst`` (``SMS1``). Gibt die Anzahl Klartext-Bytes zurück."""
    enc = StreamEncryptor(aad, chunk_size)
    dst.write(enc.header)
    total = 0
    while True:
        block = src.read(chunk_size)
        if not block:
            break
        total += len(block)
        dst.write(enc.update(block))
    dst.write(enc.finalize())
    return total


def decrypt_stream(src: IO[bytes], aad: bytes | str = b"", read_size: int = 256 * 1024) -> Iterator[bytes]:
    """Entschlüsselt eine ``SMS1``-Datei blockweise (Generator; Fehler erst beim betroffenen Block)."""
    dec = StreamDecryptor(read_stream_header(src), aad)
    while True:
        data = src.read(read_size)
        if not data:
            break
        out = dec.update(data)
        if out:
            yield out
    yield dec.finalize()


def rewrap_stream_file(path: Path) -> bool:
    """Wrappt den Datenschlüssel einer ``SMS1``-Datei mit dem aktiven Schlüssel neu (atomar ersetzt).

    Gibt ``True`` zurück, wenn die Datei geändert wurde. Die verschlüsselten Blöcke werden nur kopiert.
    """
    path = Path(path)
    tmp = path.with_name(path.name + ".rewrap.tmp")
    try:
        with open(path, "rb") as src:
            header = read_stream_header(src)
            new_header = rewrap(header)
            if new_header == header:
                return False
            with open(tmp, "wb") as dst:
                dst.write(new_header)  # type: ignore[arg-type]
                while True:
                    block = src.read(1024 * 1024)
                    if not block:
                        break
                    dst.write(block)
                dst.flush()
                os.fsync(dst.fileno())
        # erst nach dem Schließen ersetzen – Windows verbietet das Ersetzen einer noch geöffneten Datei
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return True


# --------------------------------------------------------------------------- Rotation (Registry)
Rewrapper = Callable[[Any], int]
_rewrappers: dict[str, Rewrapper] = {}


def register_rewrap(name: str, fn: Rewrapper) -> None:
    """Registriert eine Funktion ``fn(db) -> int``, die alle Tokens eines Bereichs mit :func:`rewrap` neu wrappt.

    Wird von ``cli rotate-keys`` aufgerufen (je Eintrag eigene Transaktion). Mehrfaches Registrieren desselben
    Namens ersetzt den Eintrag (Modul-Reload).
    """
    if not name or not callable(fn):
        raise ValueError("register_rewrap(name, fn) braucht einen Namen und eine Funktion")
    _rewrappers[name] = fn


def rewrappers() -> dict[str, Rewrapper]:
    return dict(_rewrappers)


def rewrap_column(db: Any, model: Any, column: str, *, batch: int = 500) -> int:
    """Hilfe für :func:`register_rewrap`: wrappt alle Tokens einer Spalte (Text- oder Binär-Tokens) neu.

    Beispiel: ``register_rewrap("messages.body_enc", lambda db: rewrap_column(db, Message, "body_enc"))``.
    Commit macht der Aufrufer (die CLI). Gibt die Anzahl geänderter Zeilen zurück.
    """
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import select, update

    pk = sa_inspect(model).primary_key
    if len(pk) != 1:
        raise ValueError("rewrap_column unterstützt nur Tabellen mit einspaltigem Primärschlüssel")
    pk_col = pk[0]
    col = getattr(model, column)
    changed = 0
    last = None
    active = active_key_id()
    while True:
        stmt = select(pk_col, col).where(col.is_not(None)).order_by(pk_col).limit(batch)
        if last is not None:
            stmt = stmt.where(pk_col > last)
        rows = db.execute(stmt).all()
        if not rows:
            break
        for ident, token in rows:
            last = ident
            if not token or not is_token(token) or key_id_of(token) == active:
                continue
            db.execute(update(model).where(pk_col == ident).values({col: rewrap(token)}))
            changed += 1
        db.flush()
    return changed


def rewrap_all(only: Iterable[str] | None = None) -> dict[str, int]:
    """Führt alle registrierten Rewrap-Funktionen aus (je eigene Transaktion) → ``{name: anzahl}``."""
    from .db import session_scope

    wanted = set(only) if only else None
    results: dict[str, int] = {}
    for name, fn in sorted(_rewrappers.items()):
        if wanted is not None and name not in wanted:
            continue
        with session_scope() as db:
            results[name] = int(fn(db) or 0)
    return results
