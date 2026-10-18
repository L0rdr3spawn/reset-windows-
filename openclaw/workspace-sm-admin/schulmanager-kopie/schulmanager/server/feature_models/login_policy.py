"""Anmelde-Richtlinien (Erweiterung 4, §11.5): wer darf sich wie anmelden (Tabelle ``login_policy_rules``).

Eine Regel gilt für einen Geltungsbereich ``scope``:

* ``default`` – alle Konten (``scope_ref`` leer),
* ``role`` – eine Rolle (``scope_ref`` = Rollenname, z. B. ``schueler``),
* ``grade`` – ein Jahrgang (``scope_ref`` = Klassenstufe als Text, z. B. ``"5"``),
* ``class`` – eine Klasse (``scope_ref`` = Klassen-ID aus dem Planungsdokument),
* ``user`` – eine Person (``scope_ref`` = Benutzer-ID als Text).

``audience`` (nur bei ``grade``/``class``) grenzt die Gruppe ein: ``alle`` | ``schueler`` (Schüler/innen der
Klasse bzw. des Jahrgangs) | ``eltern`` (Eltern dieser Schüler/innen); sonst immer ``alle``.

Felder – jeweils ``NULL`` = vom nächstallgemeineren Bereich erben (Auswertung: ``server/login_policy.py``):
``methods`` (erlaubte Anmeldewege, Liste aus ``login_policy.METHODS``, nie leer), ``required_links`` (Anbieter, die
verbunden sein müssen), ``self_link`` (darf eigene Anbieter-Konten verbinden/trennen), ``reset_channels``
(„Passwort vergessen“ per ``email``/``sms``), ``sso_create`` (beim ersten Anbieter-Login per bestätigter E-Mail zuordnen).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

SCOPES = ("default", "role", "grade", "class", "user")
AUDIENCES = ("alle", "schueler", "eltern")
AUDIENCE_SCOPES = ("grade", "class")      # nur hier ist eine Zielgruppe ≠ ``alle`` erlaubt
RULE_FIELDS = ("methods", "required_links", "self_link", "reset_channels", "sso_create")


class LoginPolicyRule(Base):
    __tablename__ = "login_policy_rules"
    __table_args__ = (UniqueConstraint("scope", "scope_ref", "audience", name="uq_login_policy_rules_scope_ref_audience"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(20), index=True)
    scope_ref: Mapped[str] = mapped_column(String(80), default="")
    audience: Mapped[str] = mapped_column(String(20), default="alle")
    methods: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    required_links: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    self_link: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    reset_channels: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    sso_create: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


# --------------------------------------------------------------------------- Ereignisse
def _mark_changed(session, _flush_context) -> None:
    """Nach dem Flush merken, ob Regeln geändert wurden (→ Cache nach dem Commit leeren)."""
    for obj in (*session.new, *session.dirty, *session.deleted):
        if isinstance(obj, LoginPolicyRule):
            session.info["login_policy_changed"] = True
            return


def _after_commit(session) -> None:
    if session.info.pop("login_policy_changed", False):
        from .. import login_policy

        login_policy.invalidate_cache()


def _after_rollback(session) -> None:
    session.info.pop("login_policy_changed", None)


def _drop_person_rules(_mapper, connection, target) -> None:
    """Konto gelöscht → seine Personen-Regeln mitlöschen (eine neu vergebene ID erbt sie nie)."""
    from sqlalchemy import delete

    from .. import login_policy

    table = LoginPolicyRule.__table__
    connection.execute(delete(table).where(table.c.scope == "user", table.c.scope_ref == str(target.id)))
    login_policy.invalidate_cache()


def _register_events() -> None:
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    from ..db_models import User

    if not event.contains(Session, "after_flush", _mark_changed):
        event.listen(Session, "after_flush", _mark_changed)
        event.listen(Session, "after_commit", _after_commit)
        event.listen(Session, "after_soft_rollback", lambda session, _tx: _after_rollback(session))
        event.listen(User, "after_delete", _drop_person_rules)


_register_events()
