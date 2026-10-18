"""Wartung: abgelaufene Sitzungen/Tokens und alte Login-Versuche löschen, optional Auto-Backup."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta

from sqlalchemy import delete

from .config import config
from .db import session_scope, utcnow
from .db_models import ApiToken, LoginAttempt, UserSession

log = logging.getLogger("schulmanager.maintenance")

LOGIN_ATTEMPT_RETENTION_DAYS = 30
_last_backup = 0.0


def run_maintenance() -> dict[str, int]:
    """Einmaliger Wartungslauf (synchron). Rückgabe: Anzahl gelöschter Einträge je Tabelle."""
    now = utcnow()
    with session_scope() as db:
        sessions = db.execute(delete(UserSession).where(UserSession.expires_at < now)).rowcount or 0
        # persönliche Tokens sofort nach Ablauf; API-Zugänge mit Umfang 30 Tage länger (Nutzungsprotokoll einsehbar)
        tokens = db.execute(delete(ApiToken).where(
            ApiToken.expires_at.is_not(None),
            ApiToken.expires_at < now,
            ApiToken.scope.is_(None))).rowcount or 0
        tokens += db.execute(delete(ApiToken).where(
            ApiToken.expires_at.is_not(None), ApiToken.expires_at < now - timedelta(days=30),
            ApiToken.scope.is_not(None))).rowcount or 0
        cutoff = now - timedelta(days=LOGIN_ATTEMPT_RETENTION_DAYS)
        attempts = db.execute(delete(LoginAttempt).where(LoginAttempt.created_at < cutoff)).rowcount or 0
    result = {"sessions": sessions, "api_tokens": tokens, "login_attempts": attempts}
    # Dateiablage (Erweiterung 2): verwaiste Uploads > 24 h, gelöschte Dateien > 30 Tage, Temp-/Blob-Reste
    try:
        from .files import cleanup as files_cleanup

        result.update(files_cleanup(now))
    except Exception:  # noqa: BLE001 - Dateiwartung darf die übrige Wartung nicht verhindern
        log.exception("Wartung der Dateiablage fehlgeschlagen")
    # Atteste/Dokumente (§9.6): Aufbewahrungsfrist SM_STUDENT_DOCS_RETENTION_DAYS
    try:
        from .routes.features_student_self import run_retention as docs_retention

        from . import retention

        result["student_documents"] = docs_retention(retention.age_days("documents", config.student_docs_retention_days))
    except Exception:  # noqa: BLE001
        log.exception("Aufbewahrungsfrist der Schüler-Dokumente fehlgeschlagen")
    # Formular-Baukasten: Erinnerungen an Prüfende, Aufbewahrungsfrist abgeschlossener Einreichungen
    try:
        from .routes.features_forms import run_reminders, run_retention as forms_retention

        result["form_reminders"] = run_reminders()
        from . import retention

        result["form_submissions"] = forms_retention(retention.age_days("forms", config.student_docs_retention_days))
    except Exception:  # noqa: BLE001
        log.exception("Wartung der Formulare fehlgeschlagen")
    # Kontakt & Wiederherstellung (§11.2): abgelaufene Codes, alte Test-Nachrichten des Test-Postausgangs
    try:
        from .routes.features_contact import cleanup as contact_cleanup

        result.update(contact_cleanup(now))
    except Exception:  # noqa: BLE001
        log.exception("Wartung der Konto-Codes fehlgeschlagen")
    # Zugangsbriefe (§11.3): abgelaufene Stapel mit (verschlüsselten) Startpasswörtern löschen
    try:
        from .letters import delete_expired as letters_cleanup

        with session_scope() as db:
            result["letter_batches"] = letters_cleanup(db, now)
    except Exception:  # noqa: BLE001
        log.exception("Wartung der Brief-Stapel fehlgeschlagen")
    # Benachrichtigungszentrale: Fristerinnerungen, zurückgestellte E-Mails/Zusammenfassung, Aufräumen
    try:
        from .notifications import run_periodic

        result.update({f"notifications_{k}": v for k, v in run_periodic(now).items()})
    except Exception:  # noqa: BLE001
        log.exception("Wartung der Benachrichtigungen fehlgeschlagen")
    # Kursraum-Papierkorb: nach ``trash_retention_days`` (Standard 30) endgültig entfernen
    try:
        from .routes.features_channel_trash import run_purge as channel_trash_purge

        result.update(channel_trash_purge(now))
    except Exception:  # noqa: BLE001
        log.exception("Wartung des Kursraum-Papierkorbs fehlgeschlagen")
    # Fehlerprotokoll aufräumen, Lauf für die Statusseite vermerken
    try:
        from .ops import prune_error_log, record_maintenance

        result["error_log"] = prune_error_log(now)
        record_maintenance(result)
    except Exception:  # noqa: BLE001
        log.exception("Wartung des Fehlerprotokolls fehlgeschlagen")
    # Löschkonzept (DSGVO): Warteliste „ausgetreten“ abgleichen, fällige Daten löschen, Alters-Fristen, Audit-Frist
    try:
        from . import retention

        result.update({f"retention_{k}": v for k, v in retention.run(now).items()})
    except Exception:  # noqa: BLE001
        log.exception("Wartung des Löschkonzepts fehlgeschlagen")
    if any(result.values()):
        log.info("Wartung: %s", result)
    return result


def _maybe_backup() -> None:
    global _last_backup
    if config.auto_backup_hours <= 0:
        return
    if time.monotonic() - _last_backup < config.auto_backup_hours * 3600:
        return
    from .backups import create_backup

    _last_backup = time.monotonic()
    create_backup()


async def maintenance_loop() -> None:
    global _last_backup
    _last_backup = time.monotonic()  # erstes Auto-Backup nach einem Intervall
    while True:
        try:
            await asyncio.to_thread(run_maintenance)
            await asyncio.to_thread(_maybe_backup)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            log.exception("Wartungslauf fehlgeschlagen")
        await asyncio.sleep(max(5.0, config.maintenance_interval))
