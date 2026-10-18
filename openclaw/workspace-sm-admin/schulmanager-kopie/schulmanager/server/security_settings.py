"""Sicherheits-Einstellungen der Schule (Tabelle ``security_settings``, Migration 0044).

* ``twofa_mode`` – Zwei-Faktor-Anmeldung für Personal: ``off`` | ``recommended`` (Voreinstellung: Hinweis auf der
  Startseite) | ``required`` (Pflicht – wer betroffen ist, durchläuft die Einrichtung unter ``/zwei-faktor``).
* ``twofa_roles`` – betroffene Rollen (Voreinstellung: Administration, Schulleitung, Sekretariat).
* ``staff_idle_minutes`` – Abmeldung des Personals nach so vielen Minuten Inaktivität (Voreinstellung 12 Stunden;
  Schüler/innen und Eltern: ``SM_SESSION_IDLE_MINUTES``).
* ``initial_password_days`` – Gültigkeit eines Startpassworts in Tagen (Voreinstellung 14).

Die Umgebungsvariable ``SM_REQUIRE_2FA_ROLES`` bleibt als feste Pflicht für die genannten Rollen bestehen.
Lesen ist zwischengespeichert (:data:`CACHE_SECONDS`); Schreiben leert den Speicher.
"""
from __future__ import annotations

import threading
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import config
from .db import utcnow
from .feature_models.security import SecuritySetting

TWOFA_MODES = ("off", "recommended", "required")
#: Rollen, für die 2FA überhaupt angeboten/verlangt werden kann
TWOFA_ROLE_CHOICES = ("admin", "schulleitung", "planer", "sekretariat", "abteilungsleitung", "lehrer")
#: Rollen mit gekürzter Sitzungsdauer (Personal) – nicht Schüler/Eltern, nicht Monitor (Anzeigegerät)
STAFF_ROLES = frozenset({"admin", "schulleitung", "planer", "sekretariat", "abteilungsleitung", "lehrer",
                         "schulbegleitung", "hausmeister"})
IDLE_RANGE = (15, 7 * 24 * 60)
PASSWORD_DAYS_RANGE = (1, 90)

DEFAULTS: dict[str, Any] = {
    "twofa_mode": "recommended",
    "twofa_roles": ["admin", "schulleitung", "sekretariat"],
    "staff_idle_minutes": 12 * 60,
    "initial_password_days": 14,
}
CACHE_SECONDS = 5.0
_lock = threading.Lock()
_cache: dict[str, Any] = {"at": 0.0, "values": None, "db": None}


class SettingError(ValueError):
    """Ungültiger Wert (deutscher Text für die Antwort 422)."""


def invalidate() -> None:
    with _lock:
        _cache.update(at=0.0, values=None, db=None)


def clean(key: str, value: Any) -> Any:
    if key == "twofa_mode":
        if value not in TWOFA_MODES:
            raise SettingError("Zwei-Faktor: „aus“, „empfohlen“ oder „Pflicht“ wählen.")
        return value
    if key == "twofa_roles":
        if not isinstance(value, list) or any(r not in TWOFA_ROLE_CHOICES for r in value):
            raise SettingError("Unbekannte Rolle bei der Zwei-Faktor-Anmeldung.")
        return [r for r in TWOFA_ROLE_CHOICES if r in value]
    if key == "staff_idle_minutes":
        lo, hi = IDLE_RANGE
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            raise SettingError(f"Abmeldung nach Inaktivität: {lo} Minuten bis {hi // 1440} Tage.")
        return value
    if key == "initial_password_days":
        lo, hi = PASSWORD_DAYS_RANGE
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            raise SettingError(f"Gültigkeit des Startpassworts: {lo} bis {hi} Tage.")
        return value
    raise SettingError(f"Unbekannte Einstellung „{key}“.")


def load(db: Session) -> dict[str, Any]:
    """Alle Einstellungen (Voreinstellungen + gespeicherte Werte), zwischengespeichert."""
    now = time.monotonic()
    which = id(db.get_bind())
    with _lock:
        if _cache["values"] is not None and _cache["db"] == which and now - _cache["at"] < CACHE_SECONDS:
            return dict(_cache["values"])
    values = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS.items()}
    for row in db.scalars(select(SecuritySetting)):
        if row.key in DEFAULTS:
            try:
                values[row.key] = clean(row.key, row.value)
            except SettingError:
                pass
    with _lock:
        _cache.update(at=now, values=values, db=which)
    return dict(values)


def save(db: Session, patch: dict[str, Any], actor_id: int | None) -> dict[str, Any]:
    """Teil-Update (ohne Commit). Wirft :class:`SettingError`."""
    for key, value in patch.items():
        value = clean(key, value)
        row = db.get(SecuritySetting, key)
        if row is None:
            db.add(SecuritySetting(key=key, value=value, updated_at=utcnow(), updated_by=actor_id))
        else:
            row.value, row.updated_at, row.updated_by = value, utcnow(), actor_id
    db.flush()
    invalidate()
    return load(db)


def twofa_policy(db: Session, role: str) -> str:
    """``required`` | ``recommended`` | ``""`` für eine Rolle."""
    if role in config.require_2fa_roles:
        return "required"
    values = load(db)
    if role in values["twofa_roles"]:
        if values["twofa_mode"] == "required":
            return "required"
        if values["twofa_mode"] == "recommended":
            return "recommended"
    return ""


def idle_minutes(db: Session | None, role: str) -> int:
    """Abmeldung nach Inaktivität für Konten dieser Rolle (Minuten)."""
    if role in STAFF_ROLES and db is not None:
        return min(int(load(db)["staff_idle_minutes"]), config.session_idle_minutes)
    return config.session_idle_minutes


def initial_password_days(db: Session) -> int:
    return int(load(db)["initial_password_days"])
