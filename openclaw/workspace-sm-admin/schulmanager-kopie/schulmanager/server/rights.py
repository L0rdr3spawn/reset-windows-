"""Rollen & Rechte pro Schule: Abweichungen vom Standard laden/speichern, wirksame Matrix, Zweige.

Die Regeln selbst (Katalog, Standard, feste Mindestregeln) stehen in :mod:`permissions`; hier liegt nur die
Datenbankanbindung. ``deps.build_auth_user`` ruft :func:`load_overrides` je Anfrage (kleine Tabelle, Index auf der Rolle).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import permissions as P
from .db import utcnow
from .db_models import Branch, ParentLink, RoleOverride, User, UserBranch


# ------------------------------------------------------------------------------------ Abweichungen
def load_overrides(db: Session, role: str) -> dict[str, tuple[bool, str | None]]:
    rows = db.execute(select(RoleOverride.permission, RoleOverride.granted, RoleOverride.scope)
                      .where(RoleOverride.role == role)).all()
    return {perm: (bool(granted), scope) for perm, granted, scope in rows}


def apply_changes(db: Session, role: str, changes: dict[str, dict[str, Any]], actor: str) -> dict[str, Any]:
    """Speichert Änderungen ``{recht: {"granted": bool, "scope": str|None}}`` oder ``{recht: None}`` (zurück auf
    Standard). Verstöße gegen feste Regeln → ``ValueError``. Rückgabe: ``{recht: "vorher → nachher"}`` fürs Protokoll."""
    if role not in P.ROLES:
        raise ValueError(f"Unbekannte Rolle: {role}")
    if role in P.READ_ONLY_ROLES or role == "monitor":
        raise ValueError("Diese Rolle ist fest vorgegeben und nicht änderbar.")
    current = load_overrides(db, role)
    before = P.effective_rights(role, False, current)
    parsed: dict[str, tuple[bool, str | None] | None] = {}
    for perm, change in changes.items():
        if change is None:
            if perm not in P.CATALOGUE:
                raise ValueError(f"Unbekanntes Recht: {perm}")
            parsed[perm] = None
            continue
        granted = bool(change.get("granted", True))
        scope = change.get("scope") or None
        err = P.validate_override(role, perm, granted, scope)
        if err:
            raise ValueError(err)
        parsed[perm] = (granted, scope)
    for perm, val in parsed.items():
        row = db.get(RoleOverride, (role, perm))
        if val is None:
            if row is not None:
                db.delete(row)
            continue
        if row is None:
            row = RoleOverride(role=role, permission=perm)
            db.add(row)
        row.granted, row.scope = val
        row.updated_at, row.updated_by = utcnow(), actor[:80]
    db.flush()
    after = P.effective_rights(role, False, load_overrides(db, role))
    diff: dict[str, Any] = {}
    for perm in sorted(set(before[0]) ^ set(after[0]) | {p for p in parsed if before[1].get(p) != after[1].get(p)}):
        def show(state: tuple[set[str], dict[str, str]]) -> str:
            return "nein" if perm not in state[0] else P.SCOPE_LABELS.get(state[1].get(perm, P.ALL), "ja")
        diff[perm] = f"{show(before)} → {show(after)}"
    return diff


def reset_role(db: Session, role: str) -> int:
    """Alle Abweichungen der Rolle löschen (zurück auf Standard). Rückgabe: Anzahl gelöschter Einträge."""
    n = len(load_overrides(db, role))
    db.execute(delete(RoleOverride).where(RoleOverride.role == role))
    return n


def effective_matrix(db: Session) -> dict[str, tuple[set[str], dict[str, str]]]:
    """Rolle → (wirksame Rechte, Umfänge) für die Erwachsenen-Variante (ohne Konto-Flag ``adult``)."""
    rows = db.execute(select(RoleOverride.role, RoleOverride.permission, RoleOverride.granted, RoleOverride.scope)).all()
    by_role: dict[str, dict[str, tuple[bool, str | None]]] = {}
    for role, perm, granted, scope in rows:
        by_role.setdefault(role, {})[perm] = (bool(granted), scope)
    return {r: P.effective_rights(r, False, by_role.get(r)) for r in P.ROLES}


def describe(db: Session) -> dict[str, Any]:
    """Alles, was die Seite „Rollen & Rechte“ braucht (``GET /api/v1/rights``)."""
    eff = effective_matrix(db)
    changed = {(r, p) for r, p in db.execute(select(RoleOverride.role, RoleOverride.permission)).all()}
    areas = [{"id": a, "label": label, "permissions": [p for p, aid in P.PERMISSION_AREA.items() if aid == a]}
             for a, label in P.AREAS]
    perms = [{"id": pid, "label": meta[1], "help": meta[2], "area": meta[0], "status": meta[4],
              "scopes": [{"id": s, "label": P.SCOPE_LABELS.get(s, s)} for s in (P.ALL, *meta[3])] if meta[3] else []}
             for pid, meta in P.CATALOGUE.items()]
    roles = []
    cells: dict[str, dict[str, dict[str, Any]]] = {}
    for role in P.ROLES:
        info = P.ROLE_INFO.get(role, {})
        editable = role not in P.READ_ONLY_ROLES and role != "monitor"
        roles.append({"id": role, "label": P.ROLE_LABELS[role], "description": info.get("description", ""),
                      "level": info.get("level", 0), "kind": info.get("kind", "staff"), "link": info.get("link"),
                      "editable": editable})
        perm_set, scopes = eff[role]
        cells[role] = {}
        for pid in P.CATALOGUE:
            lock = P.lock_info(role, pid)
            default_granted = pid in P.ROLE_PERMISSIONS[role]
            cells[role][pid] = {
                "granted": pid in perm_set, "scope": scopes.get(pid) or (P.ALL if pid in perm_set else None),
                "default_granted": default_granted, "default_scope": P.PERMISSION_SCOPES.get(role, {}).get(pid)
                or (P.ALL if default_granted else None),
                "changed": (role, pid) in changed, "locked": lock["state"] if lock else None,
                "reason": lock["reason"] if lock else None,
                "scope_options": [{"id": s, "label": P.SCOPE_LABELS.get(s, s)} for s in P.scope_options(role, pid)],
            }
    return {
        "areas": areas, "permissions": perms, "roles": roles, "cells": cells,
        "derived_roles": P.DERIVED_ROLES, "hierarchy": list(P.HIERARCHY), "scope_labels": P.SCOPE_LABELS,
        "locked_rules": LOCKED_RULES_TEXT,
    }


LOCKED_RULES_TEXT: list[str] = [
    "Die technische Administration sieht nie Atteste, Förderdaten oder gemeldete Chats.",
    "Schüler/innen, Eltern und Schulbegleitung sehen nie Daten anderer Kinder.",
    "Die Schulbegleitung hat keine Elternrechte (keine Krankmeldung, keine Atteste).",
    "Lehrkräfte sehen Schülerdaten und Pläne nur eigener (bzw. geleiteter) Klassen, Atteste nur als Klassenleitung.",
    "Ansichtskonten (Zuschauer) bleiben schreibgeschützt; Monitore zeigen nur den Vertretungsplan.",
    "Rechte verwalten, Protokoll, Lizenz und Anmelderegeln bleiben bei Administration und Schulleitung.",
    "Die Administration behält Konten-, Einstellungs-, System- und Rechteverwaltung (Schutz vor Aussperrung).",
    "Volljährige Schüler/innen melden sich nur über die Konto-Einstellung „volljährig“ selbst krank.",
]


# ------------------------------------------------------------------------------------ Zweige
def branch_dict(b: Branch) -> dict[str, Any]:
    return {"id": b.id, "name": b.name, "sites": list(b.sites or []), "grades": list(b.grades or []),
            "class_ids": list(b.class_ids or [])}


def user_branches(db: Session, user_id: int) -> list[dict[str, Any]]:
    rows = db.scalars(select(Branch).join(UserBranch, UserBranch.branch_id == Branch.id)
                      .where(UserBranch.user_id == user_id).order_by(Branch.name))
    return [branch_dict(b) for b in rows]


def set_user_branches(db: Session, user: User, branch_ids: list[int]) -> None:
    valid = set(db.scalars(select(Branch.id).where(Branch.id.in_(branch_ids)))) if branch_ids else set()
    missing = set(branch_ids) - valid
    if missing:
        raise ValueError(f"Unbekannter Zweig: {sorted(missing)[0]}")
    db.execute(delete(UserBranch).where(UserBranch.user_id == user.id))
    for bid in sorted(valid):
        db.add(UserBranch(user_id=user.id, branch_id=bid))


def user_children(db: Session, user_id: int) -> list[str]:
    """Verknüpfte Kinder (Eltern, Schulbegleitung) in Anlagereihenfolge."""
    return list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user_id)
                           .order_by(ParentLink.id)))


def set_user_children(db: Session, user: User, student_ids: list[str]) -> None:
    db.execute(delete(ParentLink).where(ParentLink.parent_user_id == user.id))
    seen: set[str] = set()
    for sid in student_ids:
        if sid not in seen:
            seen.add(sid)
            db.add(ParentLink(parent_user_id=user.id, student_id=sid))


def role_titles(school, user) -> list[str]:
    """Anzeigetitel einer Person, z. B. ``["Lehrkraft", "Klassenleitung 5a"]`` (Klassenleitung aus den Stammdaten)."""
    titles = [P.ROLE_LABELS.get(user.role, user.role)]
    if user.role in ("lehrer", "abteilungsleitung"):
        lead = sorted(P.lead_class_ids(school, user.teacher_id))
        if lead:
            names = {c.id: c.name for c in school.classes}
            titles.append("Klassenleitung " + ", ".join(names.get(c, c) for c in lead))
    if user.role == "abteilungsleitung":
        for b in getattr(user, "branches", None) or []:
            titles.append(f"Zweig {b['name']}")
    return titles
