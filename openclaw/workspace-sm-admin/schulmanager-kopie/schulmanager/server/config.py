"""Konfiguration aus Umgebungsvariablen (``SM_*``).

Das Objekt :data:`config` ist ein Singleton. :meth:`Config.reload` liest die
Umgebung neu ein (Tests, ``create_app()``), die Objektidentität bleibt dabei
erhalten, sodass ``from schulmanager.server.config import config`` überall gültig bleibt.
"""
from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path

from ..branding import PRODUCT_NAME

log = logging.getLogger("schulmanager.config")

APP_VERSION = os.environ.get("SM_APP_VERSION", "").strip() or "0.1.0"   # im Docker-Image per Build-Argument gesetzt
MODES = ("production", "demo", "development")
# Bekannte Entwicklungs-/Beispielpasswörter (scripts/dev.sh, docker-compose.dev.yml, preview.sh, Tests): im
# Echtbetrieb als SM_ADMIN_PASSWORD verboten
DEV_PASSWORDS = frozenset({"admin12345", "schulmanager-dev", "Schulmanager-Vorschau-2026", "demo123456",
                           "Ci-Sonnenblume-2026", "changeme", "password", "admin"})


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _bool(name: str, default: bool) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "ja", "on")


def _int(name: str, default: int) -> int:
    value = _env(name)
    try:
        return int(value) if value is not None else default
    except ValueError:
        raise RuntimeError(f"Umgebungsvariable {name} muss eine ganze Zahl sein (ist {value!r})") from None


def _float(name: str, default: float) -> float:
    value = _env(name)
    try:
        return float(value) if value is not None else default
    except ValueError:
        raise RuntimeError(f"Umgebungsvariable {name} muss eine Zahl sein (ist {value!r})") from None


def _is_placeholder(value: str) -> bool:
    """Platzhalter aus ``.env.example`` (``BITTE_AENDERN…``) – nie als echter Wert gültig."""
    return value.strip().upper().startswith("BITTE_AENDERN") or "CHANGE_ME" in value.upper()


def _is_local_url(url: str) -> bool:
    host = url.split("://", 1)[-1].split("/", 1)[0].rsplit("@", 1)[-1].split(":", 1)[0]
    return host in ("localhost", "127.0.0.1", "::1", "[::1]") or host.endswith(".localhost")


class ConfigError(RuntimeError):
    """Ungültige oder unsichere Konfiguration – der Server startet nicht."""


class Config:
    """Alle Einstellungen des Servers. Felder siehe :meth:`reload`."""

    def __init__(self) -> None:
        self.reload()

    # ------------------------------------------------------------------
    def reload(self) -> "Config":
        """Liest alle ``SM_*``-Variablen (neu) ein."""
        self._resolve_mode()
        self.database_url: str = _env("SM_DATABASE_URL", "sqlite:///./data/schulmanager.db") or ""
        self.data_dir: Path = Path(_env("SM_DATA_DIR", "./data") or "./data")
        self.backup_dir: Path = Path(_env("SM_BACKUP_DIR") or (self.data_dir / "backups"))
        self.backup_keep: int = _int("SM_BACKUP_KEEP", 30)
        self.auto_backup_hours: float = _float("SM_AUTO_BACKUP_HOURS", 0.0)
        self.base_url: str = (_env("SM_BASE_URL", "http://localhost:8000") or "").rstrip("/")
        self.cookie_secure: bool = _bool("SM_COOKIE_SECURE", self.env == "production")
        self.admin_user: str = _env("SM_ADMIN_USER", "admin") or "admin"
        self.admin_password: str | None = _env("SM_ADMIN_PASSWORD")
        self.load_demo: bool = _bool("SM_LOAD_DEMO", False) and self.mode != "production"
        self.demo_background: bool = _bool("SM_DEMO_BACKGROUND", True)
        self.demo_classes_per_grade: int = _int("SM_DEMO_CLASSES_PER_GRADE", 14)
        # Demo: zusätzlich ein Konto je Lehrkraft, Schüler/in und Elternhaus (Postfach/Chats mit allen testen)
        self.demo_all_accounts: bool = _bool("SM_DEMO_ALL_ACCOUNTS", True)
        # Vorführ-Instanz mit simulierten Daten: Demo-Zugänge gibt der Inhaber aus (``/demo-access``), Demo-Konten
        # und Systemfunktionen sind geschützt (``deps._guard_demo``); die Instanz wird regelmäßig neu aufgesetzt.
        self.demo_public: bool = _bool("SM_DEMO_PUBLIC", self.mode == "demo") and self.mode != "production"
        # Lizenz (``licensing``): öffentlicher Prüfschlüssel des Anbieters (Ed25519, base64), Lizenzdatei,
        # Durchsetzung (Nur-Lesen bei gesperrter/abgelaufener Lizenz, Kontenlimit) – Standard nur in Produktion.
        # Threads für synchrone Endpunkte (anyio) und Datenbank-Pool (PostgreSQL): Pool > Threads, sonst Verklemmung
        self.threadpool: int = max(8, _int("SM_THREADPOOL", 40))
        self.db_pool_size: int = max(5, _int("SM_DB_POOL_SIZE", 20))
        self.license_pubkey: str = _env("SM_LICENSE_PUBKEY", "") or ""
        self.license_file: str = _env("SM_LICENSE_FILE", "") or ""
        # Betriebsmodus ``production``: Durchsetzung immer an, ``SM_LICENSE_ENFORCE`` wird dort ignoriert (sonst könnte
        # jede Schule die Sperre mit einer Umgebungsvariablen abschalten). Entwicklung/Demo: frei, Standard aus.
        self.license_enforce_requested: bool = _bool("SM_LICENSE_ENFORCE", self.env == "production")
        self.license_enforce: bool = True if self.mode == "production" else self.license_enforce_requested
        # Fristen, falls die Lizenz keine eigenen nennt: Kulanzzeit (nur lesen) nach Ablauf bzw. nach Ende der
        # Offline-Toleranz; Toleranz in Tagen seit der letzten erfolgreichen Online-Bestätigung.
        self.license_grace_days: int = max(0, _int("SM_LICENSE_GRACE_DAYS", 14))
        # Prüfrhythmus: ausführliche Prüfung mindestens alle 24 h und beim Start; dazu alle 15 Minuten eine kurze
        # Statusabfrage (``ping``: kein Datenbankzugriff, winzige Anfrage), damit eine Sofortsperre zeitnah wirkt (0 = aus).
        self.license_check_hours: int = max(1, _int("SM_LICENSE_CHECK_HOURS", 24))
        self.license_ping_minutes: int = max(0, _int("SM_LICENSE_PING_MINUTES", 15))
        self.license_server: str = _env("SM_LICENSE_SERVER", "") or ""
        self.auto_migrate: bool = _bool("SM_AUTO_MIGRATE", True)
        self.frontend_dist: Path = Path(_env("SM_FRONTEND_DIST", "frontend/dist") or "frontend/dist")
        self.log_level: str = (_env("SM_LOG_LEVEL", "INFO") or "INFO").upper()
        self.log_format: str = (_env("SM_LOG_FORMAT", "json" if self.env == "production" else "text")
                                or "text").lower()
        self.access_log: bool = _bool("SM_ACCESS_LOG", True)
        self.generate_time_limit: float = _float("SM_GENERATE_TIME_LIMIT", 30.0)
        # Auto-Planer (server/autoplan.py): repariert den Stundenplan nach Änderungen automatisch
        self.autoplan: bool = _bool("SM_AUTOPLAN", True)
        # Ferien/Feiertage automatisch aus öffentlicher API übernehmen (server/holiday_import.py)
        self.holiday_import: bool = _bool("SM_HOLIDAY_IMPORT", True)
        self.autoplan_delay: float = _float("SM_AUTOPLAN_DELAY", 3.0)          # Sekunden Ruhe nach der letzten Änderung
        self.autoplan_time_limit: float = _float("SM_AUTOPLAN_TIME_LIMIT", 15.0)  # Rechenzeit des Generators
        self.keep_versions: int = max(2, _int("SM_KEEP_VERSIONS", 300))

        # SMTP / Benachrichtigungen (genutzt von server/notify.py)
        self.smtp_host: str | None = _env("SM_SMTP_HOST")
        self.smtp_port: int = _int("SM_SMTP_PORT", 587)
        self.smtp_user: str | None = _env("SM_SMTP_USER")
        self.smtp_password: str | None = _env("SM_SMTP_PASSWORD")
        self.smtp_from: str | None = _env("SM_SMTP_FROM")
        self.smtp_tls: str = (_env("SM_SMTP_TLS", "starttls") or "starttls").lower()  # starttls|ssl|none
        self.webhook_secret: str | None = _env("SM_WEBHOOK_SECRET")
        self.notify_dispatcher: bool = _bool("SM_NOTIFY_DISPATCHER", True)
        # SMS & Test-Postausgang (§11.2, server/sms.py, server/auth_messages.py)
        self.sms_provider: str = (_env("SM_SMS_PROVIDER", "") or "").lower()  # leer|log|webhook|twilio|seven
        self.sms_url: str | None = _env("SM_SMS_URL")                    # webhook: POST {to, text}
        self.sms_token: str | None = _env("SM_SMS_TOKEN")                # webhook (Bearer) / twilio / seven
        self.sms_account_sid: str | None = _env("SM_SMS_ACCOUNT_SID")    # twilio
        self.sms_from: str | None = _env("SM_SMS_FROM")                  # Absender (twilio Pflicht, seven optional)
        self.sms_timeout: float = _float("SM_SMS_TIMEOUT", 10.0)
        # Test-Postausgang: E-Mails/SMS nur anzeigen (/test-postausgang) statt zustellen – in Produktion verboten.
        # Standard nur bei lokaler Adresse: eine aus dem Internet erreichbare Instanz würde sonst Rücksetz-Codes
        # öffentlich zeigen (Fund 2026-10-16, Heimserver im Entwicklungsmodus).
        self.dev_outbox: bool = _bool("SM_DEV_OUTBOX", self.env != "production" and _is_local_url(self.base_url))
        self.auth_code_minutes: int = _int("SM_AUTH_CODE_MINUTES", 15)   # Gültigkeit von Codes/Links
        self._warned_sms: bool = False
        # Postfach ↔ E-Mail (server/mailbridge.py): Abruf verbundener Konten, Anmeldung über Google/Microsoft
        self.mail_sync: bool = _bool("SM_MAIL_SYNC", True)
        self.mail_sync_minutes: float = _float("SM_MAIL_SYNC_MINUTES", 5.0)
        self.oauth_google_client_id: str | None = _env("SM_OAUTH_GOOGLE_CLIENT_ID")
        self.oauth_google_client_secret: str | None = _env("SM_OAUTH_GOOGLE_CLIENT_SECRET")
        self.oauth_microsoft_client_id: str | None = _env("SM_OAUTH_MICROSOFT_CLIENT_ID")
        self.oauth_microsoft_client_secret: str | None = _env("SM_OAUTH_MICROSOFT_CLIENT_SECRET")
        self.oauth_microsoft_tenant: str = _env("SM_OAUTH_MICROSOFT_TENANT", "common") or "common"

        # Sitzungen & Anmeldung
        self.session_idle_minutes: int = _int("SM_SESSION_IDLE_MINUTES", 7 * 24 * 60)
        self.session_max_days: int = _int("SM_SESSION_MAX_DAYS", 30)
        self.login_max_failures: int = _int("SM_LOGIN_MAX_FAILURES", 5)
        self.login_max_failures_ip: int = _int("SM_LOGIN_MAX_FAILURES_IP", 30)
        self.login_lock_minutes: int = _int("SM_LOGIN_LOCK_MINUTES", 15)
        # Rollen, für die Zwei-Faktor-Anmeldung Pflicht ist (z. B. "admin,schulleitung,planer,sekretariat")
        self.require_2fa_roles: frozenset[str] = frozenset(
            r.strip() for r in os.environ.get("SM_REQUIRE_2FA_ROLES", "").split(",") if r.strip())
        # Ausnahmen vom SSRF-Schutz (net_guard): schulinterne Ziele für Mailserver/Webhooks/SSO/SMS, kommagetrennt
        # (Hostname, IP oder Netz, optional ``:port``) – z. B. "mail.schule.lokal,10.20.0.0/24"
        self.outbound_allow: str = _env("SM_OUTBOUND_ALLOW", "") or ""
        self.trust_proxy: bool = _bool("SM_TRUST_PROXY", False)
        self.proxy_count: int = max(1, _int("SM_PROXY_COUNT", 1))
        # Adressen/Netze, deren X-Forwarded-* geglaubt wird (S-10); leer = nur Loopback. Alter Name als Rückfall.
        self.trusted_proxies: str = (_env("SM_TRUSTED_PROXIES") or _env("SM_FORWARDED_ALLOW_IPS") or "").strip()
        self.scrypt_n: int = _int("SM_SCRYPT_N", 2 ** 15)
        self.app_name: str = _env("SM_APP_NAME", PRODUCT_NAME) or PRODUCT_NAME

        # Laufzeit
        self.sse_ping_seconds: float = _float("SM_SSE_PING_SECONDS", 20.0)
        self.maintenance_interval: float = _float("SM_MAINTENANCE_INTERVAL", 3600.0)
        # >>> UPDATES-HA (docs/UPDATES-UND-HOCHVERFUEGBARKEIT.md): mehrere Knoten mit gemeinsamer Datenbank/Ablage
        # SM_NODE_ID: Name dieses Knotens (Leader-Sperre, Drain-Datei); SM_HA=1: Hintergrundjobs nur auf dem Leader-Knoten
        self.node_id: str = (_env("SM_NODE_ID", "") or "main")[:40]
        self.ha: bool = _bool("SM_HA", False)
        # <<< UPDATES-HA
        # OpenAPI-Doku: im ausdrücklichen Betriebsmodus ``production`` standardmäßig aus (sichere Voreinstellung)
        # SM_ENABLE_DOCS: ``0`` aus · ``admin`` nur angemeldete Administratoren · ``1``/``public`` für alle (S-15).
        # Ohne Angabe: im ausdrücklichen Betriebsmodus ``production`` aus, sonst ``admin``.
        raw_docs = (_env("SM_ENABLE_DOCS") or "").lower()
        if raw_docs in ("admin", "admins"):
            self.docs_mode: str = "admin"
        elif raw_docs in ("1", "true", "yes", "on", "public"):
            self.docs_mode = "public"
        elif raw_docs in ("0", "false", "no", "off"):
            self.docs_mode = "off"
        else:
            self.docs_mode = "off" if (self.mode == "production" and self.mode_explicit) else "admin"
        self.enable_docs: bool = self.docs_mode != "off"
        self.metrics_token: str | None = _env("SM_METRICS_TOKEN")

        # OIDC (optional)
        self.oidc_issuer: str | None = _env("SM_OIDC_ISSUER")
        self.oidc_client_id: str | None = _env("SM_OIDC_CLIENT_ID")
        self.oidc_client_secret: str | None = _env("SM_OIDC_CLIENT_SECRET")
        self.oidc_scopes: str = _env("SM_OIDC_SCOPES", "openid profile email") or "openid profile email"
        self.oidc_username_claim: str = _env("SM_OIDC_USERNAME_CLAIM", "preferred_username") or "preferred_username"
        self.oidc_auto_create: bool = _bool("SM_OIDC_AUTO_CREATE", False)
        self.oidc_default_role: str = _env("SM_OIDC_DEFAULT_ROLE", "lehrer") or "lehrer"
        self.oidc_label: str = _env("SM_OIDC_LABEL", "Single Sign-on") or "Single Sign-on"
        # Anmeldedienste Microsoft/Google/Apple (§11.4, server/sso_providers.py) – Vorrang vor der Einrichtung im
        # Admin-Bereich (Tabelle sso_providers); Weiterleitungs-URI: {SM_BASE_URL}/api/v1/auth/sso/<anbieter>/callback
        self.sso_microsoft_client_id: str | None = _env("SM_SSO_MICROSOFT_CLIENT_ID")
        self.sso_microsoft_client_secret: str | None = _env("SM_SSO_MICROSOFT_CLIENT_SECRET")
        self.sso_microsoft_tenant: str | None = _env("SM_SSO_MICROSOFT_TENANT")   # Standard „organizations“
        self.sso_google_client_id: str | None = _env("SM_SSO_GOOGLE_CLIENT_ID")
        self.sso_google_client_secret: str | None = _env("SM_SSO_GOOGLE_CLIENT_SECRET")
        self.sso_google_hd: str | None = _env("SM_SSO_GOOGLE_HD")                 # nur Konten dieser Domain
        self.sso_apple_client_id: str | None = _env("SM_SSO_APPLE_CLIENT_ID")     # Services-ID
        self.sso_apple_team_id: str | None = _env("SM_SSO_APPLE_TEAM_ID")
        self.sso_apple_key_id: str | None = _env("SM_SSO_APPLE_KEY_ID")
        self.sso_apple_private_key: str | None = _env("SM_SSO_APPLE_PRIVATE_KEY")  # PEM-Inhalt oder Dateipfad (.p8)
        # Test-Anbieter (nicht eingerichtete Anbieter simulieren) – Standard an in Entwicklung, in Produktion verboten
        self.sso_dev_mock: bool = _bool("SM_SSO_DEV_MOCK", False)

        # Verschlüsselung & Dateiablage (Erweiterung 2, siehe server/crypto.py und server/files.py)
        # SM_ENCRYPTION_KEYS="kid:<base64 32 Byte>,…" (erster = aktiv) – in Produktion Pflicht
        self.encryption_keys: str | None = _env("SM_ENCRYPTION_KEYS")
        self.files_dir: Path = Path(_env("SM_FILES_DIR") or (self.data_dir / "files"))
        self.upload_max_mb: float = _float("SM_UPLOAD_MAX_MB", 25.0)
        self.quota_mb_staff: float = _float("SM_QUOTA_MB_STAFF", 2000.0)
        self.quota_mb_student: float = _float("SM_QUOTA_MB_STUDENT", 200.0)
        # Chat-Bildanhänge (DB-Blobs, S-13): Kontingent je Konto und je Chat in MB (0 = unbegrenzt) + Rate je 10 Minuten
        self.chat_quota_mb_staff: float = _float("SM_CHAT_QUOTA_MB_STAFF", 500.0)
        self.chat_quota_mb_student: float = _float("SM_CHAT_QUOTA_MB_STUDENT", 100.0)
        self.chat_quota_mb_chat: float = _float("SM_CHAT_QUOTA_MB_CHAT", 1000.0)
        self.chat_uploads_per_10min: int = _int("SM_CHAT_UPLOADS_PER_10MIN", 30)
        self.clamav_host: str | None = _env("SM_CLAMAV_HOST")
        self.clamav_port: int = _int("SM_CLAMAV_PORT", 3310)
        self.clamav_required: bool = _bool("SM_CLAMAV_REQUIRED", False)
        self.clamav_timeout: float = _float("SM_CLAMAV_TIMEOUT", 30.0)
        # Atteste/Dokumente von Schüler/innen (§9.6): nach N Tagen samt Datei löschen (0 = nie)
        self.student_docs_retention_days: int = _int("SM_STUDENT_DOCS_RETENTION_DAYS", 400)

        self._warned = False
        self._warned_mode = False
        self._secret_key_env: str | None = _env("SM_SECRET_KEY")
        self._secret_key: str | None = self._secret_key_env
        return self

    # ------------------------------------------------------------------
    def _resolve_mode(self) -> None:
        """Betriebsmodus ``SM_MODE`` = ``production`` | ``demo`` | ``development`` (siehe docs/INSTALLATION.md).

        * ``production`` – echte Schule: ``SM_ENV`` wird ``production``, Demo-Funktionen sind aus, Pflicht-Secrets
          werden beim Start geprüft (:meth:`mode_problems`).
        * ``demo`` – Vorführ-Instanz: Demo-Zugänge/-Schutz an (``SM_DEMO_PUBLIC`` standardmäßig 1).
        * ``development`` – lokale Entwicklung/Tests.
        Ohne ``SM_MODE`` bleibt alles wie bisher: Modus aus ``SM_ENV`` und ``SM_DEMO_PUBLIC`` abgeleitet
        (``mode_explicit`` = False; dann gelten die neuen Prüfungen nur als Warnung).
        """
        raw = (_env("SM_MODE") or "").lower()
        env_raw = (_env("SM_ENV") or "").lower()
        self.mode_error: str | None = None
        self.mode_explicit: bool = bool(raw)
        if raw and raw not in MODES:
            self.mode_error = f"SM_MODE muss production, demo oder development sein (ist {raw!r})"
            raw = ""
            self.mode_explicit = False
        if raw == "production":
            if env_raw and env_raw != "production":
                self.mode_error = (f"SM_MODE=production widerspricht SM_ENV={env_raw} – "
                                   "SM_ENV weglassen oder production setzen")
            self.env: str = "production"
            self.mode: str = "production"
        elif raw in ("demo", "development"):
            self.env = env_raw or "development"
            if raw == "development" and self.env == "production":
                self.mode_error = "SM_MODE=development widerspricht SM_ENV=production"
            self.mode = raw
        else:
            self.env = env_raw or "development"
            demo_flag = _bool("SM_DEMO_PUBLIC", False)
            self.mode = "demo" if demo_flag else ("production" if self.env == "production" else "development")

    @property
    def is_production_mode(self) -> bool:
        """Echtbetrieb: Demo-Funktionen (Demo laden, Demo-Zugänge, Demo-Konten) sind abgeschaltet."""
        return self.mode == "production"

    def mode_problems(self) -> tuple[list[str], list[str]]:
        """(Fehler, Warnungen) der Konfiguration für den Betriebsmodus. Fehler brechen den Start ab – im
        ausdrücklichen ``SM_MODE=production``; bei abgeleitetem Modus (altes ``SM_ENV=production``) sind es
        Warnungen."""
        errors: list[str] = []
        warnings: list[str] = []
        if self.mode_error:
            errors.append(self.mode_error)
        if self.mode != "production":
            return errors, warnings
        strict = self.mode_explicit
        bad: list[str] = []
        key = self._secret_key_env or ""
        if not key:
            bad.append("SM_SECRET_KEY fehlt (erzeugen mit `openssl rand -hex 32`)")
        elif len(key) < 32 or _is_placeholder(key):
            bad.append("SM_SECRET_KEY ist zu kurz oder noch der Platzhalter aus .env.example (mind. 32 Zeichen)")
        if not self.encryption_keys:
            bad.append("SM_ENCRYPTION_KEYS fehlt (erzeugen mit `python -m schulmanager.server.cli gen-key`; "
                       "Schlüssel getrennt vom Backup aufbewahren)")
        elif _is_placeholder(self.encryption_keys):
            bad.append("SM_ENCRYPTION_KEYS ist noch der Platzhalter aus .env.example")
        if not _env("SM_BASE_URL"):
            bad.append("SM_BASE_URL fehlt (öffentliche Adresse, z. B. https://plan.meine-schule.de)")
        elif not self.base_url.startswith("https://") and not _is_local_url(self.base_url):
            bad.append("SM_BASE_URL muss mit https:// beginnen")
        if not self.cookie_secure:
            bad.append("SM_COOKIE_SECURE=0 ist im Echtbetrieb nicht erlaubt (Sitzungs-Cookie nur über HTTPS)")
        if self.admin_password and (self.admin_password in DEV_PASSWORDS or _is_placeholder(self.admin_password)):
            bad.append("SM_ADMIN_PASSWORD ist ein bekanntes Entwicklungs-/Beispielpasswort – ein eigenes wählen "
                       "oder die Variable leer lassen (dann wird ein Einmalpasswort erzeugt)")
        if _bool("SM_LOAD_DEMO", False):
            bad.append("SM_LOAD_DEMO=1 ist im Echtbetrieb nicht erlaubt (Demo-Daten gehören nicht in eine "
                       "echte Schule)")
        if _bool("SM_DEMO_PUBLIC", False):
            bad.append("SM_DEMO_PUBLIC=1 ist im Echtbetrieb nicht erlaubt (Demo-Zugänge nur im Modus demo)")
        if self.db_kind == "sqlite":
            warnings.append("SQLite ist für kleine Schulen ausreichend; ab etwa 500 Konten empfiehlt sich PostgreSQL")
        if not self.smtp_enabled:
            warnings.append("Kein E-Mail-Versand eingerichtet (SM_SMTP_HOST/SM_SMTP_FROM) – Passwort-zurücksetzen, "
                            "Benachrichtigungen und Briefe per E-Mail funktionieren nicht")
        if not self.require_2fa_roles:
            warnings.append("SM_REQUIRE_2FA_ROLES ist leer – Zwei-Faktor-Anmeldung für Administration und "
                            "Schulleitung wird empfohlen (admin,schulleitung,sekretariat)")
        if self.auto_backup_hours <= 0:
            warnings.append("Keine automatische App-Sicherung (SM_AUTO_BACKUP_HOURS=0) – tägliche Sicherung über "
                            "den Backup-Container bzw. Timer einrichten")
        (errors if strict else warnings).extend(bad)
        return errors, warnings

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return not self.is_production

    @property
    def db_kind(self) -> str:
        """``sqlite`` oder ``postgresql`` (bzw. der Dialektname)."""
        scheme = self.database_url.split(":", 1)[0].split("+", 1)[0]
        return "postgresql" if scheme.startswith("postgres") else scheme

    @property
    def oidc_enabled(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_client_id)

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    @property
    def secret_key(self) -> str:
        """Geheimer Schlüssel (HMAC für Token-Hashes, OIDC-State).

        Produktion: ``SM_SECRET_KEY`` ist Pflicht. Entwicklung: wird einmalig in
        ``<data_dir>/.secret_key`` erzeugt und wiederverwendet.
        """
        if self._secret_key:
            return self._secret_key
        if self.is_production:
            raise ConfigError("SM_SECRET_KEY muss in Produktion gesetzt sein")
        path = self.data_dir / ".secret_key"
        try:
            if path.exists():
                self._secret_key = path.read_text().strip()
            if not self._secret_key:
                path.parent.mkdir(parents=True, exist_ok=True)
                self._secret_key = secrets.token_urlsafe(48)
                path.write_text(self._secret_key)
                try:
                    path.chmod(0o600)
                except OSError:
                    pass
        except OSError:
            self._secret_key = secrets.token_urlsafe(48)
        return self._secret_key

    def validate(self) -> None:
        """Prüft die Konfiguration; wirft :class:`ConfigError` bei unsicheren Werten in Produktion."""
        errors, warnings = self.mode_problems()
        if errors:
            raise ConfigError("Die Konfiguration ist für den Betriebsmodus %s unvollständig oder unsicher – "
                              "der Start wird abgebrochen:\n  - %s\nHilfe: docs/INSTALLATION.md und .env.example"
                              % (self.mode, "\n  - ".join(errors)))
        if warnings and not self._warned_mode:
            for w in warnings:
                log.warning("Konfiguration: %s", w)
            self._warned_mode = True
        if self.env not in ("development", "production"):
            raise ConfigError(f"SM_ENV muss 'development' oder 'production' sein (ist {self.env!r})")
        if self.is_production:
            if not self._secret_key_env:
                raise ConfigError("SM_SECRET_KEY muss in Produktion gesetzt sein (z. B. `openssl rand -hex 32`)")
            if len(self._secret_key_env) < 32:
                raise ConfigError("SM_SECRET_KEY ist zu kurz (mindestens 32 Zeichen)")
            if not self._warned and not self.cookie_secure:
                log.warning("SM_COOKIE_SECURE=0 in Produktion – Cookies werden auch über HTTP gesendet!")
            if not self._warned and not self.base_url.startswith("https://"):
                log.warning("SM_BASE_URL beginnt nicht mit https:// – iCal-Links/SSO nutzen diese Adresse")
            self._warned = True
        if self.scrypt_n < 2 or self.scrypt_n & (self.scrypt_n - 1):
            raise ConfigError("SM_SCRYPT_N muss eine Zweierpotenz sein")
        if self.is_production and self.scrypt_n < 2 ** 14:
            raise ConfigError("SM_SCRYPT_N ist für Produktion zu klein (mindestens 16384)")
        self._validate_files()
        self._validate_contact()
        self._validate_sso()

    def _validate_sso(self) -> None:
        """Anmeldedienste (§11.4): Test-Anbieter nie in Produktion."""
        if self.sso_dev_mock and (self.env != "development" or self.demo_public or self.mode == "demo"):
            raise ConfigError("SM_SSO_DEV_MOCK=1 ist nur in der Entwicklung erlaubt (SM_ENV=development, nicht Demo, "
                              "nicht Produktion) – der Test-Anbieter meldet ohne Prüfung beliebige E-Mail-Adressen an")

    def _validate_contact(self) -> None:
        """SMS-Anbieter und Test-Postausgang (§11.2)."""
        if self.is_production and self.dev_outbox:
            raise ConfigError("SM_DEV_OUTBOX=1 ist in Produktion verboten – der Test-Postausgang zeigt Codes und "
                              "Links öffentlich an")
        if self.sms_provider not in ("", "log", "webhook", "twilio", "seven"):
            raise ConfigError(f"SM_SMS_PROVIDER muss leer, log, webhook, twilio oder seven sein "
                              f"(ist {self.sms_provider!r})")
        if self.sms_provider == "webhook" and not (self.sms_url or "").startswith(("https://", "http://")):
            raise ConfigError("SM_SMS_PROVIDER=webhook braucht SM_SMS_URL (http(s)://…)")
        if self.sms_provider == "twilio" and not (self.sms_account_sid and self.sms_token and self.sms_from):
            raise ConfigError("SM_SMS_PROVIDER=twilio braucht SM_SMS_ACCOUNT_SID, SM_SMS_TOKEN und SM_SMS_FROM")
        if self.sms_provider == "seven" and not self.sms_token:
            raise ConfigError("SM_SMS_PROVIDER=seven braucht SM_SMS_TOKEN (API-Schlüssel von seven.io)")
        if self.sms_timeout <= 0:
            raise ConfigError("SM_SMS_TIMEOUT muss größer als 0 sein")
        if not 1 <= self.auth_code_minutes <= 1440:
            raise ConfigError("SM_AUTH_CODE_MINUTES muss zwischen 1 und 1440 liegen")
        if self._warned_sms:
            return
        if self.is_production and self.sms_provider == "log":
            log.warning("SM_SMS_PROVIDER=log in Produktion – SMS werden nicht verschickt, nur protokolliert")
        if self.dev_outbox and (self.smtp_enabled or self.sms_provider):
            log.warning("SM_DEV_OUTBOX=1: Konto-E-Mails/SMS werden trotz SMTP/SMS-Einstellung NICHT zugestellt, "
                        "sondern unter /test-postausgang angezeigt")
        self._warned_sms = True

    def _validate_files(self) -> None:
        """Verschlüsselung und Datei-Uploads (Erweiterung 2)."""
        if self.is_production and not self.encryption_keys:
            raise ConfigError("SM_ENCRYPTION_KEYS muss in Produktion gesetzt sein – Schlüssel erzeugen mit "
                              "`python -m schulmanager.server.cli gen-key` und GETRENNT vom Backup sicher aufbewahren")
        if self.encryption_keys:
            from .crypto import parse_keys  # später Import: crypto importiert config

            parse_keys(self.encryption_keys)
        if not 0 < self.upload_max_mb <= 10240:
            raise ConfigError("SM_UPLOAD_MAX_MB muss zwischen 0 und 10240 liegen")
        if self.quota_mb_staff < 0 or self.quota_mb_student < 0:
            raise ConfigError("SM_QUOTA_MB_STAFF/SM_QUOTA_MB_STUDENT dürfen nicht negativ sein")
        if min(self.chat_quota_mb_staff, self.chat_quota_mb_student, self.chat_quota_mb_chat) < 0                 or self.chat_uploads_per_10min < 0:
            raise ConfigError("SM_CHAT_QUOTA_MB_* und SM_CHAT_UPLOADS_PER_10MIN dürfen nicht negativ sein")
        if not 0 < self.clamav_port < 65536:
            raise ConfigError("SM_CLAMAV_PORT muss eine Portnummer sein")
        if self.clamav_timeout <= 0:
            raise ConfigError("SM_CLAMAV_TIMEOUT muss größer als 0 sein")
        if self.clamav_required and not self.clamav_host:
            raise ConfigError("SM_CLAMAV_REQUIRED=1 braucht SM_CLAMAV_HOST")

    def public_dict(self) -> dict:
        """Nicht geheime Werte (für ``/admin/system``)."""
        return {
            "env": self.env,
            "mode": self.mode,
            "database": self.db_kind,
            "database_url": mask_url(self.database_url),
            "base_url": self.base_url,
            "cookie_secure": self.cookie_secure,
            "data_dir": str(self.data_dir),
            "backup_dir": str(self.backup_dir),
            "frontend_dist": str(self.frontend_dist),
            "generate_time_limit": self.generate_time_limit,
            "keep_versions": self.keep_versions,
            "smtp_enabled": self.smtp_enabled,
            "sms_enabled": bool(self.sms_provider),
            "sms_provider": self.sms_provider or None,
            "dev_outbox": self.dev_outbox,
            "oidc_enabled": self.oidc_enabled,
            "auto_migrate": self.auto_migrate,
            "session_idle_minutes": self.session_idle_minutes,
            "session_max_days": self.session_max_days,
            "encryption_keys_configured": bool(self.encryption_keys),
            "files_dir": str(self.files_dir),
            "upload_max_mb": self.upload_max_mb,
            "quota_mb_staff": self.quota_mb_staff,
            "quota_mb_student": self.quota_mb_student,
            "chat_quota_mb_staff": self.chat_quota_mb_staff,
            "chat_quota_mb_student": self.chat_quota_mb_student,
            "chat_quota_mb_chat": self.chat_quota_mb_chat,
            "clamav_enabled": bool(self.clamav_host),
            "clamav_required": self.clamav_required,
            "student_docs_retention_days": self.student_docs_retention_days,
        }


def mask_url(url: str) -> str:
    """Entfernt ein Passwort aus einer Datenbank-URL."""
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        creds, host = rest.rsplit("@", 1)
        user = creds.split(":", 1)[0]
        return f"{scheme}://{user}:***@{host}"
    return url


config = Config()
