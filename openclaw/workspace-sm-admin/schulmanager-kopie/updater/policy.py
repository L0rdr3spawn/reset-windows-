"""Reine Regeln des Update-Agenten (ohne Netz und ohne Docker – einzeln testbar).

* :func:`canonical` / :func:`verify_signed` – Ed25519-Prüfung mit dem **fest hinterlegten** Anbieter-Schlüssel.
* :func:`check_release` – nimmt ein Release nur an, wenn Signatur, Form, Downgrade-Schutz, Mindestversion und
  Registry-Vorgabe stimmen. Der Agent führt **nie** etwas anderes aus als „Version X installieren“.
* :func:`after_update` / :func:`after_image_rollback` – Entscheidung nach einem Gesundheitstest.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

STRICT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
IMAGE_REF = re.compile(r"^[a-z0-9][a-z0-9._/:-]{0,200}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FILE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_pubkey(text: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(text.strip()))


def fingerprint(text: str) -> str:
    return hashlib.sha256(base64.b64decode(text.strip())).hexdigest()[:16]


def verify_signed(pub: Ed25519PublicKey, obj: Any, signature: str) -> bool:
    try:
        pub.verify(base64.b64decode(signature or ""), canonical(obj))
        return True
    except (InvalidSignature, ValueError):
        return False


def version_key(text: str | None) -> tuple[int, ...]:
    m = re.match(r"^v?(\d+(?:\.\d+){0,3})", (text or "").strip())
    if not m:
        return (0, 0, 0, 0)
    parts = [int(p) for p in m.group(1).split(".")]
    return tuple(parts + [0] * (4 - len(parts)))


@dataclass
class Verdict:
    ok: bool
    reason: str = ""


def check_release(manifest: Any, signature: str, pub: Ed25519PublicKey, *, installed: str, highest_installed: str = "",
                  allowed_registry: str = "") -> Verdict:
    """Prüft ein vom Anbieter angebotenes Release.

    * Signatur über das gesamte Manifest (Ed25519, fester Schlüssel),
    * Form (Produkt, Version, Verteilung: Download mit SHA-256 **oder** Registry mit Digest),
    * **Downgrade-Schutz**: nur Versionen, die größer sind als die laufende **und** als die höchste je installierte,
    * Mindestversion: die laufende Version muss ``min_version`` erreichen,
    * optional nur Abbilder aus ``allowed_registry`` (Präfix).
    """
    if not isinstance(manifest, dict) or not verify_signed(pub, manifest, signature):
        return Verdict(False, "Signatur des Releases ungültig")
    if manifest.get("product") != "schulpuls":
        return Verdict(False, "Fremdes Produkt")
    version = str(manifest.get("version", ""))
    if not STRICT_VERSION.match(version):
        return Verdict(False, "Ungültige Versionsangabe")
    if version_key(version) <= version_key(installed):
        return Verdict(False, "Downgrade-Schutz: Version ist nicht neuer als die laufende")
    if highest_installed and version_key(version) <= version_key(highest_installed):
        return Verdict(False, "Downgrade-Schutz: Version ist nicht neuer als die höchste bisher installierte")
    minimum = str(manifest.get("min_version") or "")
    if minimum and version_key(installed) < version_key(minimum):
        return Verdict(False, f"Mindestversion {minimum} nicht erreicht")
    dist = manifest.get("dist")
    if not isinstance(dist, dict):
        return Verdict(False, "Keine Verteilungsangabe")
    if dist.get("type") == "download":
        if not SHA256.match(str(dist.get("sha256", ""))) or not FILE_NAME.match(str(dist.get("file", ""))):
            return Verdict(False, "Ungültige Download-Angabe")
        if not isinstance(dist.get("size"), int) or dist["size"] <= 0:
            return Verdict(False, "Ungültige Größenangabe")
    elif dist.get("type") == "registry":
        image, digest = str(dist.get("image", "")), str(dist.get("digest", ""))
        if not IMAGE_REF.match(image) or not DIGEST.match(digest):
            return Verdict(False, "Ungültige Registry-Angabe")
        if allowed_registry and not image.startswith(allowed_registry):
            return Verdict(False, "Registry nicht erlaubt")
    else:
        return Verdict(False, "Unbekannte Verteilungsart")
    mig = manifest.get("migration")
    if not isinstance(mig, dict) or not isinstance(mig.get("present"), bool) or not isinstance(mig.get("backward_compatible"), bool):
        return Verdict(False, "Ungültige Migrationsangabe")
    return Verdict(True)


# --------------------------------------------------------------------------- Rollback
def after_update(healthy: bool) -> str:
    """``keep`` | ``rollback`` nach dem Gesundheitstest der neuen Version."""
    return "keep" if healthy else "rollback"


def after_image_rollback(*, old_healthy: bool, migration_present: bool, backward_compatible: bool,
                         allow_db_restore: bool, has_backup: bool) -> str:
    """Wie geht es nach dem Zurückstellen des alten Abbilds weiter?

    * ``done`` – alte Version läuft gesund und das Schema passt (keine oder abwärtskompatible Migration),
    * ``restore_db`` – Sicherung einspielen (Migration nicht abwärtskompatibel oder alte Version läuft nicht),
      nur wenn kein anderer Server die Datenbank gerade nutzt (``allow_db_restore``) und eine Sicherung existiert,
    * ``give_up`` – nichts Sicheres mehr zu tun: Fehler melden, der Anbieter bzw. die Administration entscheidet.
    """
    needs_restore = (migration_present and not backward_compatible) or not old_healthy
    if not needs_restore:
        return "done"
    if allow_db_restore and has_backup:
        return "restore_db"
    return "give_up"
