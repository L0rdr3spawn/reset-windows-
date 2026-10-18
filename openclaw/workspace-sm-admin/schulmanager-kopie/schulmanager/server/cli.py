"""Betriebs-CLI: ``python -m schulmanager.server.cli <befehl>``.

Befehle::

    migrate                                   Datenbank migrieren (alembic upgrade head)
    migrate-chats [--dry-run|--rollback|--force] Postfach-Gruppen/-Chats nach Chats & Gruppen übernehmen
    create-admin --username U [--password-stdin] [--display-name N] [--update]
    reset-password --username U [--password-stdin]   (ohne Passwort: Startpasswort wird ausgegeben)
    unlock --username U                       Login-Sperre aufheben (Fehlversuche löschen)
    disable-2fa --username U
    list-users [--role R]
    check-config                              Konfiguration/Betriebsmodus prüfen (ohne Start)
    load-demo [--time-limit S] [--classes-per-grade N] [--no-accounts]
    backup                                    Sicherung nach SM_BACKUP_DIR
    maintenance                               Abgelaufene Sitzungen/Tokens löschen
    gen-key [--kid ID]                        Neuen Master-Schlüssel für SM_ENCRYPTION_KEYS ausgeben
    rotate-keys [--only NAME]                 Alle Datenschlüssel mit dem aktiven Master-Schlüssel neu wrappen
    crypto-status                             Aktiver Schlüssel, Schlüssel-IDs, Fingerabdrücke (ohne Geheimnisse)
    verify-files [--limit N]                  Alle Dateiinhalte entschlüsseln und Prüfsummen vergleichen

Die Umgebung (``SM_DATABASE_URL`` usw.) gilt wie beim Server.
"""
from __future__ import annotations

import argparse
import getpass
import logging
import sys

from sqlalchemy import delete, select

from . import db as dbmod
from . import migrate
from .accounts import create_user, revoke_sessions
from .audit import audit
from .config import config
from .db_models import LoginAttempt, User
from .security import TEMP_PASSWORD_N, generate_password, hash_password, password_problems, set_totp_secret


def _init(migrate_db: bool = True) -> None:
    config.validate()
    dbmod.configure_engine()
    if migrate_db:
        migrate.upgrade_head()


def _read_password(args, role: str, username: str) -> str | None:
    if not getattr(args, "password_stdin", False):
        return None
    if sys.stdin.isatty():
        password = getpass.getpass("Passwort: ")
    else:
        password = sys.stdin.readline().rstrip("\r\n")
    problems = password_problems(password, role, username)
    if problems:
        raise SystemExit("Fehler: " + " ".join(problems))
    return password


def _find(db, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username.lower()))
    if user is None:
        raise SystemExit(f"Fehler: Benutzer {username!r} existiert nicht")
    return user


def cmd_migrate(_args) -> int:
    _init(False)
    before = migrate.current_revision()
    migrate.upgrade_head()
    print(f"Datenbank {config.db_kind}: {before or '(leer)'} → {migrate.current_revision()}")
    return 0


def cmd_create_admin(args) -> int:
    _init()
    password = _read_password(args, "admin", args.username)
    with dbmod.session_scope() as db:
        existing = db.scalar(select(User).where(User.username == args.username.lower()))
        if existing is not None:
            if not args.update:
                raise SystemExit(f"Fehler: {args.username!r} existiert bereits (--update setzt Rolle/Passwort neu)")
            existing.role = "admin"
            existing.active = True
            temp = None
            if password is None:
                temp = generate_password(4, 4)
                existing.password_hash = hash_password(temp)
                existing.must_change_password = True
            else:
                existing.password_hash = hash_password(password)
                existing.must_change_password = False
            revoke_sessions(db, existing.id)
            audit(db, None, "user.cli_admin_update", f"user:{existing.id}", {"username": existing.username})
            print(f"Admin {existing.username!r} aktualisiert.")
        else:
            user, temp = create_user(db, username=args.username, role="admin",
                                     display_name=args.display_name or "Administrator", password=password,
                                     must_change_password=password is None)
            audit(db, None, "user.cli_admin_create", f"user:{user.id}", {"username": user.username})
            print(f"Admin {user.username!r} angelegt.")
    if temp:
        print(f"Startpasswort (muss beim ersten Login geändert werden): {temp}")
    return 0


def cmd_reset_password(args) -> int:
    _init()
    with dbmod.session_scope() as db:
        user = _find(db, args.username)
        password = _read_password(args, user.role, user.username)
        if password is None:
            temp = generate_password()
            user.password_hash = hash_password(temp, n=min(TEMP_PASSWORD_N, config.scrypt_n))
            user.must_change_password = True
        else:
            temp = None
            user.password_hash = hash_password(password)
            user.must_change_password = False
        revoke_sessions(db, user.id)
        db.execute(delete(LoginAttempt).where(LoginAttempt.username == user.username))
        audit(db, None, "user.cli_reset_password", f"user:{user.id}", {"username": user.username})
    print(f"Passwort von {args.username!r} zurückgesetzt." + (f" Startpasswort: {temp}" if temp else ""))
    return 0


def cmd_unlock(args) -> int:
    _init()
    with dbmod.session_scope() as db:
        n = db.execute(delete(LoginAttempt).where(LoginAttempt.username == args.username.lower(),
                                                  LoginAttempt.success.is_(False))).rowcount
    print(f"{n} Fehlversuche von {args.username!r} gelöscht.")
    return 0


def cmd_disable_2fa(args) -> int:
    _init()
    with dbmod.session_scope() as db:
        user = _find(db, args.username)
        user.totp_enabled = False
        set_totp_secret(user, None)
        audit(db, None, "user.cli_disable_2fa", f"user:{user.id}", {"username": user.username})
    print(f"2FA für {args.username!r} deaktiviert.")
    return 0


def cmd_list_users(args) -> int:
    _init()
    with dbmod.SessionLocal() as db:
        stmt = select(User).order_by(User.role, User.username)
        if args.role:
            stmt = stmt.where(User.role == args.role)
        for u in db.scalars(stmt):
            flags = ",".join(f for f, on in (("inaktiv", not u.active), ("2fa", u.totp_enabled),
                                             ("pw-wechsel", u.must_change_password)) if on)
            print(f"{u.id:6d}  {u.role:13s} {u.username:30s} {u.display_name}  {flags}")
    return 0


def cmd_check_config(_args) -> int:
    """Prüft die Konfiguration, ohne zu starten (Installation: vor dem ersten ``docker compose up``)."""
    config.reload()
    errors, warnings = config.mode_problems()
    try:
        config.validate()
    except Exception as exc:  # noqa: BLE001 - ConfigError: Meldung ausgeben
        print(f"FEHLER (Betriebsmodus {config.mode}): {exc}")
        for w in warnings:
            print(f"Hinweis: {w}")
        return 1
    print(f"Konfiguration in Ordnung (Betriebsmodus {config.mode}, Datenbank {config.db_kind}).")
    for w in warnings:
        print(f"Hinweis: {w}")
    return 0


def cmd_load_demo(args) -> int:
    if config.is_production_mode:
        print("Fehler: Demo-Funktionen sind im Echtbetrieb (SM_MODE=production) abgeschaltet.")
        return 2
    _init()
    from .demo_loader import load_demo
    from .runtime import ensure_started

    ensure_started()
    result = load_demo(None, args.time_limit, not args.no_accounts, args.classes_per_grade)
    stats = {k: v for k, v in result["stats"].items() if k != "warnings"}
    print(f"Demo-Schule geladen (Version {result['version']}): {stats}")
    for a in result["accounts"]:
        state = f"neu, Passwort {a['password']}" if a["created"] else "vorhanden"
        print(f"  {a['username']:14s} {a['role']:13s} {state}")
    return 0


def cmd_backup(_args) -> int:
    _init()
    from .backups import create_backup
    from .runtime import ensure_started

    ensure_started()
    info = create_backup()
    print(f"Sicherung {info['name']} ({info['size']} Bytes) in {config.backup_dir}")
    return 0


def cmd_maintenance(_args) -> int:
    _init()
    from .maintenance import run_maintenance

    print(run_maintenance())
    return 0


def cmd_migrate_chats(args) -> int:
    """Postfach-Gruppen/-Einzelchats nach „Chats & Gruppen“ übernehmen bzw. zurücknehmen (siehe chat_migration)."""
    _init()
    from . import chat_migration as cm

    _load_feature_modules()
    ids = args.id or None
    with dbmod.session_scope() as db:
        if args.rollback:
            print(cm.rollback(db, ids))
        else:
            print(cm.migrate_postfach(db, force=args.force, conversation_ids=ids, dry_run=args.dry_run))
    return 0


def cmd_gen_key(args) -> int:
    """Gibt einen neuen Eintrag ``id:base64`` aus (stdout); Hinweise auf stderr."""
    from .crypto import generate_key

    try:
        entry = generate_key(args.kid)
    except ValueError as exc:
        raise SystemExit(f"Fehler: {exc}") from None
    print(entry)
    print("\nNeuen Schlüssel VORN in SM_ENCRYPTION_KEYS eintragen (z. B. SM_ENCRYPTION_KEYS=\"<neu>,<alt>\"),\n"
          "Server neu starten und danach `rotate-keys` ausführen. Schlüssel GETRENNT von den Backups sicher\n"
          "aufbewahren (Passwort-Tresor) – ohne Schlüssel sind verschlüsselte Daten unwiederbringlich verloren.",
          file=sys.stderr)
    return 0


def _load_feature_modules() -> list[str]:
    """Lädt Feature-Modelle und -Router, damit sich alle ``crypto.register_rewrap``-Einträge registrieren."""
    import importlib
    import pkgutil

    from . import db_models  # noqa: F401 - lädt auch feature_models
    from . import files as _files  # noqa: F401 - registriert stored_files
    from . import routes

    loaded = []
    for mod in pkgutil.iter_modules(routes.__path__):
        if mod.name.startswith("_"):
            continue
        try:
            importlib.import_module(f"schulmanager.server.routes.{mod.name}")
            loaded.append(mod.name)
        except Exception as exc:  # noqa: BLE001
            print(f"Warnung: routes/{mod.name}.py nicht geladen ({exc.__class__.__name__}: {exc})", file=sys.stderr)
    return loaded


def cmd_rotate_keys(args) -> int:
    _init()
    from . import crypto

    _load_feature_modules()
    info = crypto.describe()
    if info["source"] == "derived" and config.is_production:
        raise SystemExit("Fehler: SM_ENCRYPTION_KEYS fehlt")
    print(f"Aktiver Schlüssel: {info['active']} (bekannt: {', '.join(info['key_ids'])})")
    names = sorted(crypto.rewrappers())
    if args.only:
        unknown = set(args.only) - set(names)
        if unknown:
            raise SystemExit(f"Fehler: unbekannte Bereiche {sorted(unknown)} – vorhanden: {names}")
    results = crypto.rewrap_all(args.only or None)
    for name, count in results.items():
        print(f"  {name:40s} {count:8d} neu gewrappt")
    with dbmod.session_scope() as db:
        audit(db, None, "system.rotate_keys", info["active"], {"results": results})
    print("Fertig. Alte Schlüssel erst entfernen, wenn keine benötigte Sicherung sie mehr braucht.")
    return 0


def cmd_crypto_status(_args) -> int:
    config.validate()
    from . import crypto

    info = crypto.describe()
    print(f"Quelle: {'abgeleitet (Entwicklung)' if info['source'] == 'derived' else 'SM_ENCRYPTION_KEYS'}")
    print(f"Aktiv:  {info['active']}")
    for kid in info["key_ids"]:
        print(f"  {kid:32s} Fingerabdruck {info['fingerprints'][kid]}")
    return 0


def cmd_verify_files(args) -> int:
    _init()
    from .files import verify_all

    result = verify_all(args.limit)
    print(f"In Ordnung: {result['ok']}, fehlend: {len(result['missing'])}, beschädigt: {len(result['corrupt'])}")
    for file_id in result["missing"][:50]:
        print(f"  fehlt:      {file_id}")
    for file_id in result["corrupt"][:50]:
        print(f"  beschädigt: {file_id}")
    return 0 if not result["missing"] and not result["corrupt"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m schulmanager.server.cli", description="Schulmanager-Betrieb")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="Datenbank migrieren").set_defaults(fn=cmd_migrate)
    p = sub.add_parser("create-admin", help="Admin-Konto anlegen")
    p.add_argument("--username", required=True)
    p.add_argument("--display-name")
    p.add_argument("--password-stdin", action="store_true", help="Passwort von stdin lesen")
    p.add_argument("--update", action="store_true", help="vorhandenes Konto zum Admin machen/Passwort setzen")
    p.set_defaults(fn=cmd_create_admin)
    p = sub.add_parser("reset-password", help="Passwort zurücksetzen")
    p.add_argument("--username", required=True)
    p.add_argument("--password-stdin", action="store_true")
    p.set_defaults(fn=cmd_reset_password)
    p = sub.add_parser("unlock", help="Login-Sperre aufheben")
    p.add_argument("--username", required=True)
    p.set_defaults(fn=cmd_unlock)
    p = sub.add_parser("disable-2fa", help="Zwei-Faktor-Anmeldung abschalten")
    p.add_argument("--username", required=True)
    p.set_defaults(fn=cmd_disable_2fa)
    p = sub.add_parser("list-users", help="Konten auflisten")
    p.add_argument("--role")
    p.set_defaults(fn=cmd_list_users)
    sub.add_parser("check-config", help="Konfiguration prüfen (Betriebsmodus, Pflicht-Secrets)").set_defaults(
        fn=cmd_check_config)
    p = sub.add_parser("load-demo", help="Demo-Schule laden")
    p.add_argument("--time-limit", type=float, default=None)
    p.add_argument("--classes-per-grade", type=int, default=14)
    p.add_argument("--no-accounts", action="store_true")
    p.set_defaults(fn=cmd_load_demo)
    sub.add_parser("backup", help="Sicherung erstellen").set_defaults(fn=cmd_backup)
    sub.add_parser("maintenance", help="Wartungslauf").set_defaults(fn=cmd_maintenance)
    mc = sub.add_parser("migrate-chats", help="Postfach-Gruppen/-Einzelchats nach Chats & Gruppen übernehmen")
    mc.add_argument("--dry-run", action="store_true", help="nur zählen, nichts ändern")
    mc.add_argument("--rollback", action="store_true", help="Übernahme zurücknehmen (Originale im Postfach einblenden)")
    mc.add_argument("--force", action="store_true", help="auch bereits geprüfte Unterhaltungen erneut prüfen")
    mc.add_argument("--id", type=int, action="append", help="nur diese Unterhaltung (mehrfach möglich)")
    mc.set_defaults(fn=cmd_migrate_chats)
    p = sub.add_parser("gen-key", help="Neuen Master-Schlüssel für SM_ENCRYPTION_KEYS ausgeben")
    p.add_argument("--kid", help="Schlüssel-ID (Standard: kJJJJMMTT)")
    p.set_defaults(fn=cmd_gen_key)
    p = sub.add_parser("rotate-keys", help="Datenschlüssel mit dem aktiven Master-Schlüssel neu wrappen")
    p.add_argument("--only", action="append", metavar="NAME", help="nur diesen Bereich (mehrfach möglich)")
    p.set_defaults(fn=cmd_rotate_keys)
    sub.add_parser("crypto-status", help="Schlüsselring anzeigen (ohne Geheimnisse)").set_defaults(fn=cmd_crypto_status)
    p = sub.add_parser("verify-files", help="Dateiinhalte prüfen (Entschlüsselung + Prüfsumme)")
    p.add_argument("--limit", type=int, default=None)
    p.set_defaults(fn=cmd_verify_files)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        return int(args.fn(args) or 0)
    finally:
        dbmod.dispose_engine()


if __name__ == "__main__":
    sys.exit(main())
