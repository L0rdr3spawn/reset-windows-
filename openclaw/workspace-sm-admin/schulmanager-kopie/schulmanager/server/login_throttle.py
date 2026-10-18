"""Drosselung der Anmeldung (S-04): progressive Verzögerung statt harter Kontosperre.

Eine harte Sperre je Benutzername ließe jede Person ein fremdes Konto gezielt aussperren (fünf falsche Passwörter
alle 15 Minuten). Stattdessen drosseln drei Zähler – jeweils mit **wachsender Wartezeit** (``BASE_DELAY`` · 2^n, höchstens
``SM_LOGIN_LOCK_MINUTES``), gemessen ab dem letzten Fehlversuch der Gruppe:

1. **Benutzername + IP** (``SM_LOGIN_MAX_FAILURES`` Fehlversuche, Standard 5): wer rät, wird gebremst – die Inhaberin
   von einer anderen IP bleibt unberührt.
2. **IP insgesamt** (``SM_LOGIN_MAX_FAILURES_IP``, Standard 30): Durchprobieren vieler Konten von einem Anschluss.
3. **Konto insgesamt** (4 × ``SM_LOGIN_MAX_FAILURES``) – wirkt **nur auf unbekannte IPs**, also nicht auf Adressen, von
   denen sich das Konto zuletzt erfolgreich angemeldet hat (verteiltes Raten ohne Aussperren der Inhaberin).

Gedrosselte Anfragen zählen nicht als Fehlversuch (wer wartet, verlängert nichts). Ein erfolgreicher Login des Kontos
(auch über SSO oder „Passwort vergessen“) setzt die Zähler zurück. Der sichere Weg für Inhaber/innen bleibt immer
offen: Passwort-Reset und SSO kennen keine Drosselung. Die Verwaltung sieht aktive Drosselungen und hebt sie auf
(``/login-locks``).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .config import config
from .db import utcnow
from .db_models import LoginAttempt

BASE_DELAY = 30            # Sekunden bei Erreichen der Schwelle; danach verdoppelt
ACCOUNT_FACTOR = 4         # Konto insgesamt: Schwelle = Faktor × Fehlversuche je Paar
KNOWN_IP_DAYS = 60


@dataclass(frozen=True)
class Throttle:
    wait: int = 0              # Sekunden bis zum nächsten Versuch (0 = frei)
    scope: str = ""            # pair | ip | account


def _cap() -> int:
    return max(BASE_DELAY, config.login_lock_minutes * 60)


def delay_for(excess: int) -> int:
    """Wartezeit bei ``excess`` Fehlversuchen über der Schwelle (0 = genau erreicht)."""
    return min(BASE_DELAY * (2 ** max(0, min(excess, 20))), _cap())


def _remaining(last: datetime | None, excess: int, now: datetime) -> int:
    if last is None:
        return 0
    return max(0, int((last + timedelta(seconds=delay_for(excess)) - now).total_seconds()) + 1)


def _window(now: datetime) -> datetime:
    return now - timedelta(minutes=config.login_lock_minutes)


def _last_success(db: Session, username: str, since: datetime) -> datetime | None:
    return db.scalar(select(func.max(LoginAttempt.created_at))
                     .where(LoginAttempt.username == username, LoginAttempt.success.is_(True),
                            LoginAttempt.created_at >= since))


def _failures(db: Session, *conds, since: datetime) -> tuple[int, datetime | None]:
    row = db.execute(select(func.count(LoginAttempt.id), func.max(LoginAttempt.created_at))
                     .where(LoginAttempt.success.is_(False), LoginAttempt.created_at > since, *conds)).one()
    return int(row[0] or 0), row[1]


def known_ip(db: Session, username: str, ip: str | None) -> bool:
    """Hat sich das Konto zuletzt von dieser IP erfolgreich angemeldet?"""
    if not ip:
        return False
    since = utcnow() - timedelta(days=KNOWN_IP_DAYS)
    return bool(db.scalar(select(func.count(LoginAttempt.id)).where(
        LoginAttempt.username == username, LoginAttempt.ip == ip, LoginAttempt.success.is_(True),
        LoginAttempt.created_at >= since)))


def status(db: Session, username: str, ip: str | None) -> Throttle:
    now = utcnow()
    window = _window(now)
    maxf = max(1, config.login_max_failures)
    best = Throttle()

    def consider(wait: int, scope: str) -> None:
        nonlocal best
        if wait > best.wait:
            best = Throttle(wait, scope)

    ok = _last_success(db, username, window)
    since = max(window, ok) if ok else window
    pair_cond = [LoginAttempt.username == username]
    pair_cond.append(LoginAttempt.ip == ip if ip else LoginAttempt.ip.is_(None))
    n, last = _failures(db, *pair_cond, since=since)
    if n >= maxf:
        consider(_remaining(last, n - maxf, now), "pair")
    if ip:
        n, last = _failures(db, LoginAttempt.ip == ip, since=window)
        if n >= config.login_max_failures_ip:
            consider(_remaining(last, n - config.login_max_failures_ip, now), "ip")
    n, last = _failures(db, LoginAttempt.username == username, since=since)
    if n >= ACCOUNT_FACTOR * maxf and not known_ip(db, username, ip):
        consider(_remaining(last, n - ACCOUNT_FACTOR * maxf, now), "account")
    return best


def record(db: Session, username: str, ip: str | None, success: bool) -> None:
    db.add(LoginAttempt(username=username[:80], ip=ip, success=success, created_at=utcnow()))
    db.commit()


# =========================================================================== Verwaltung
def active_locks(db: Session) -> list[dict]:
    """Aktuell gedrosselte Benutzernamen und IPs (für die Verwaltung)."""
    now = utcnow()
    window = _window(now)
    maxf = max(1, config.login_max_failures)
    out: list[dict] = []
    pairs = db.execute(select(LoginAttempt.username, LoginAttempt.ip, func.count(LoginAttempt.id),
                              func.max(LoginAttempt.created_at))
                       .where(LoginAttempt.success.is_(False), LoginAttempt.created_at > window)
                       .group_by(LoginAttempt.username, LoginAttempt.ip)).all()
    for username, ip, n, last in pairs:
        ok = _last_success(db, username, window)
        if ok and last and ok >= last:
            continue
        if n >= maxf:
            wait = _remaining(last, n - maxf, now)
            if wait > 0:
                out.append({"kind": "user", "username": username, "ip": ip, "failures": int(n), "wait": wait,
                            "last_failure": last})
    accounts = db.execute(select(LoginAttempt.username, func.count(LoginAttempt.id),
                                 func.max(LoginAttempt.created_at))
                          .where(LoginAttempt.success.is_(False), LoginAttempt.created_at > window)
                          .group_by(LoginAttempt.username)).all()
    for username, n, last in accounts:
        if n >= ACCOUNT_FACTOR * maxf:
            wait = _remaining(last, n - ACCOUNT_FACTOR * maxf, now)
            if wait > 0:
                out.append({"kind": "account", "username": username, "ip": None, "failures": int(n), "wait": wait,
                            "last_failure": last})
    ips = db.execute(select(LoginAttempt.ip, func.count(LoginAttempt.id), func.max(LoginAttempt.created_at))
                     .where(LoginAttempt.success.is_(False), LoginAttempt.created_at > window,
                            LoginAttempt.ip.is_not(None))
                     .group_by(LoginAttempt.ip)).all()
    for ip, n, last in ips:
        if n >= config.login_max_failures_ip:
            wait = _remaining(last, n - config.login_max_failures_ip, now)
            if wait > 0:
                out.append({"kind": "ip", "username": None, "ip": ip, "failures": int(n), "wait": wait,
                            "last_failure": last})
    return sorted(out, key=lambda r: -r["wait"])


def clear_user(db: Session, username: str) -> int:
    """Hebt alle Drosselungen eines Benutzernamens auf (löscht seine Fehlversuche)."""
    return db.execute(delete(LoginAttempt).where(LoginAttempt.username == username.lower()[:80],
                                                 LoginAttempt.success.is_(False))).rowcount or 0


def clear_ip(db: Session, ip: str) -> int:
    return db.execute(delete(LoginAttempt).where(LoginAttempt.ip == ip, LoginAttempt.success.is_(False))).rowcount or 0
