"""Erststart: Erst-Admin, Planungsdokument, optional Demo-Schule."""
from __future__ import annotations

import logging
import threading

from sqlalchemy import func, select

from .accounts import normalize_username
from .config import config
from .db import session_scope
from .db_models import User
from .security import generate_password, hash_password, password_problems

log = logging.getLogger("schulmanager.bootstrap")

DEV_ADMIN_PASSWORD = "admin12345"
_demo_thread: threading.Thread | None = None


def ensure_admin() -> str | None:
    """Legt den Erst-Admin an, wenn noch kein Konto existiert. Gibt ein erzeugtes Passwort zurück."""
    with session_scope() as db:
        if (db.scalar(select(func.count(User.id))) or 0) > 0:
            return None
        generated = None
        if config.admin_password:
            password, must_change = config.admin_password, False
            problems = password_problems(password, "admin", config.admin_user)
            if problems:
                log.warning("SM_ADMIN_PASSWORD erfüllt die Passwortregeln nicht: %s", " ".join(problems))
        elif config.is_production:
            password = generated = generate_password(4, 4)
            must_change = True
            log.warning("ERST-ADMIN angelegt: Benutzername %r, Einmalpasswort %s – bei der ersten Anmeldung muss ein "
                        "eigenes Passwort gesetzt werden, danach startet der Einrichtungsassistent "
                        "(oder SM_ADMIN_PASSWORD setzen)", config.admin_user, password)
        else:
            password, must_change = DEV_ADMIN_PASSWORD, True
            log.warning("Erst-Admin %r mit Entwicklungs-Passwort %r angelegt (Passwortwechsel beim ersten Login)",
                        config.admin_user, password)
        db.add(User(username=normalize_username(config.admin_user) or "admin", display_name="Administrator",
                    role="admin", password_hash=hash_password(password), must_change_password=must_change,
                    active=True, totp_enabled=False, adult=False))
        log.info("Erst-Admin %r angelegt", config.admin_user)
        return generated


def _demo_wanted() -> bool:
    from .store import get_store

    store = get_store()
    school = store.school
    return config.load_demo and not config.is_production_mode and not school.classes and not school.teachers and store.count_versions() <= 1


def _load_demo_safe() -> None:
    from .demo_loader import load_demo

    try:
        load_demo(None, classes_per_grade=max(1, min(23, config.demo_classes_per_grade)))
    except Exception:  # noqa: BLE001
        log.exception("Demo-Schule konnte nicht geladen werden")


def run() -> None:
    """Wird einmal pro Prozess beim Start aufgerufen (nach der Migration)."""
    global _demo_thread
    from .store import get_store

    ensure_admin()
    get_store()  # lädt bzw. legt das leere Planungsdokument an
    if _demo_wanted():
        log.warning("SM_LOAD_DEMO=1: Demo-Schule wird erzeugt (Generator läuft %.0f s)", config.generate_time_limit)
        if config.demo_background:
            _demo_thread = threading.Thread(target=_load_demo_safe, name="sm-demo", daemon=True)
            _demo_thread.start()
        else:
            _load_demo_safe()
