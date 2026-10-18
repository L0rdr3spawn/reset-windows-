"""Anmelde-Richtlinien verwalten (ARCHITECTURE.md §11.5) – Recht ``login_policy.manage`` (admin, schulleitung).

* ``GET /login-policies`` – alle Regeln + Auswahl (Rollen, Jahrgänge, Klassen, Anbieter, Wege, Kanäle, Zielgruppen)
* ``PUT /login-policies/{scope}/{ref}?audience=`` – Regel anlegen/ersetzen (alle Felder ``null`` = Regel entfernen);
  ``scope=default`` mit ``ref`` ``-`` (oder ``PUT /login-policies/default``)
* ``DELETE /login-policies/{scope}/{ref}?audience=`` – Regel entfernen
* ``GET /login-policies/effective?user_id=`` | ``?class_id=&audience=`` | ``?grade=&audience=`` | ``?role=`` –
  wirksame Richtlinie mit Herkunft je Feld („Was gilt für …?“)
* ``GET /login-policies/report?class_id=&audience=`` – Schüler/innen bzw. Eltern der Klasse, denen
  Pflicht-Verknüpfungen fehlen (mit Zählung)

Regeln für die Rolle ``admin`` und für einzelne Admin-Konten darf nur die Administration festlegen. Ohne erlaubtes
Passwort und ohne verbundenen erlaubten Anbieter würde man sich selbst aussperren → 409 (Admin ist geschützt).
Jede Änderung wird protokolliert (``login_policy.set`` / ``login_policy.delete``).
"""
from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import login_policy as lp
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import ParentLink, User
from schulmanager.server.deps import AuthUser, client_ip, require
from schulmanager.server.feature_models.login_policy import AUDIENCE_SCOPES, AUDIENCES, SCOPES, LoginPolicyRule
from schulmanager.server.permissions import ROLES

router = APIRouter(tags=["Anmelde-Richtlinien"])

PERM = "login_policy.manage"
DEFAULT_REFS = ("", "-", "_", "default")


class RuleBody(BaseModel):
    """Felder einer Regel – jeweils ``null`` = erben."""
    methods: Optional[list[str]] = Field(default=None, max_length=10)
    required_links: Optional[list[str]] = Field(default=None, max_length=10)
    self_link: Optional[bool] = None
    reset_channels: Optional[list[str]] = Field(default=None, max_length=5)
    sso_create: Optional[bool] = None
    note: str = Field(default="", max_length=500)


# =================================================================== Hilfen
def _natural(value: str) -> tuple:
    return tuple((0, int(x), "") if x.isdigit() else (1, 0, x.lower()) for x in re.split(r"(\d+)", value or "") if x)


def _school():
    from schulmanager.server.store import get_store

    return get_store().school


def _grades(school) -> list[str]:
    return sorted({str(c.grade) for c in school.classes}, key=lambda g: (len(g), g))


def _person(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "username": user.username, "display_name": user.display_name or user.username,
            "role": user.role, "active": bool(user.active)}


def _check_admin_target(actor: AuthUser, target_role: str | None) -> None:
    if target_role == "admin" and actor.role != "admin":
        raise HTTPException(403, "Regeln für die Administration darf nur die Administration festlegen.")


def _target(db: Session, actor: AuthUser, scope: str, ref: str, audience: str | None, *,
            must_exist: bool = True) -> tuple[str, str]:
    """Prüft Geltungsbereich, Bezug und Zielgruppe → ``(scope_ref, audience)`` (normalisiert)."""
    if scope not in SCOPES:
        raise HTTPException(422, f"Unbekannter Geltungsbereich „{scope}“.")
    audience = audience or "alle"
    if audience not in AUDIENCES:
        raise HTTPException(422, f"Unbekannte Zielgruppe „{audience}“.")
    if scope not in AUDIENCE_SCOPES and audience != "alle":
        raise HTTPException(422, "Eine Zielgruppe (Schüler/innen, Eltern) gibt es nur bei Jahrgängen und Klassen.")
    ref = (ref or "").strip()
    if scope == "default":
        if ref not in DEFAULT_REFS:
            raise HTTPException(422, "Die Standard-Regel hat keinen Bezug.")
        return "", "alle"
    if scope == "role":
        if ref not in ROLES:
            raise HTTPException(422, f"Unbekannte Rolle „{ref}“.")
        _check_admin_target(actor, ref)
        return ref, audience
    if scope == "grade":
        if not ref.isdigit():
            raise HTTPException(422, "Jahrgang als Zahl angeben (z. B. 5).")
        ref = str(int(ref))
        if must_exist and ref not in _grades(_school()):
            raise HTTPException(422, f"Jahrgang {ref} gibt es im Planungsdokument nicht.")
        return ref, audience
    if scope == "class":
        if must_exist and ref not in _school().index("classes"):
            raise HTTPException(422, f"Klasse „{ref}“ gibt es im Planungsdokument nicht.")
        return ref, audience
    # scope == "user"
    if not ref.isdigit():
        raise HTTPException(422, "Person über ihre Benutzer-ID angeben.")
    user = db.get(User, int(ref))
    if user is None:
        if must_exist:
            raise HTTPException(422, "Dieses Konto gibt es nicht.")
    else:
        _check_admin_target(actor, user.role)
    return str(int(ref)), audience


def _values(rule: LoginPolicyRule | None) -> dict[str, Any]:
    return {name: (getattr(rule, name) if rule is not None else None) for name in lp.FIELDS}


def _rule_out(rule: LoginPolicyRule, *, classes: dict, users: dict[int, User], names: dict[int, str],
              grades: set[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"id": rule.id, "scope": rule.scope, "ref": rule.scope_ref, "audience": rule.audience,
                           **{name: getattr(rule, name) for name in lp.FIELDS}, "note": rule.note or "",
                           "updated_at": iso(rule.updated_at),
                           "updated_by": ({"id": rule.updated_by, "name": names.get(rule.updated_by, "")}
                                          if rule.updated_by else None),
                           "orphan": False, "target": None}
    if rule.scope == "class":
        cls = classes.get(rule.scope_ref)
        out["orphan"] = cls is None
        out["target"] = {"id": rule.scope_ref, "name": cls.name if cls else rule.scope_ref,
                         "grade": str(cls.grade) if cls else None}
        out["label"] = lp.scope_label("class", rule.scope_ref, rule.audience,
                                      class_name=cls.name if cls else None)
    elif rule.scope == "user":
        user = users.get(int(rule.scope_ref)) if rule.scope_ref.isdigit() else None
        out["orphan"] = user is None
        out["target"] = _person(user)
        out["label"] = lp.scope_label("user", rule.scope_ref, person=(user.display_name or user.username)
                                      if user else None)
    else:
        if rule.scope == "grade":
            out["orphan"] = rule.scope_ref not in grades
        out["label"] = lp.scope_label(rule.scope, rule.scope_ref, rule.audience)
    return out


def _providers_info(db: Session) -> list[dict]:
    from schulmanager.server import identities

    available = {}
    try:
        for item in identities.available_providers(db) or []:
            if isinstance(item, dict) and item.get("id"):
                available[str(item["id"])] = item
    except Exception:  # noqa: BLE001 – Anzeige; Anbieter-Modul kann gerade nicht auswerten
        available = {}
    return [{"id": p, "label": identities.PROVIDER_LABELS.get(p, p), "available": p in available,
             "mock": bool(available.get(p, {}).get("mock"))} for p in identities.PROVIDERS]


def _channels_info() -> list[dict]:
    from schulmanager.server import auth_messages

    def ok(fn) -> bool:
        try:
            return bool(fn())
        except Exception:  # noqa: BLE001
            return False
    state = {"email": ok(auth_messages.email_available), "sms": ok(auth_messages.sms_available)}
    return [{"id": c, "label": lp.CHANNEL_LABELS[c], "available": state.get(c, False)} for c in lp.RESET_CHANNELS]


def _find(db: Session, scope: str, ref: str, audience: str) -> LoginPolicyRule | None:
    return db.scalar(select(LoginPolicyRule).where(LoginPolicyRule.scope == scope, LoginPolicyRule.scope_ref == ref,
                                                   LoginPolicyRule.audience == audience))


def _self_lockout(db: Session, actor: AuthUser, key: tuple[str, str, str], values: dict | None) -> str | None:
    """Würde sich der (nicht-admin) Aufrufer mit der geänderten Regel selbst aussperren? → Begründung oder ``None``."""
    if actor.role == "admin":
        return None
    rules = dict(lp.load_rules(db))
    if values is None:
        rules.pop(key, None)
    else:
        rules[key] = values
    policy = lp.effective_policy(db, actor, rules=rules)
    from schulmanager.server import identities

    linked = set(identities.linked_providers(db, actor.id) or ())
    available = lp.available_provider_ids(db)
    # Ein verbundener Anbieter hilft nur, wenn er erlaubt UND gerade eingerichtet ist (sonst kein Anmeldeweg)
    if "password" not in policy.methods and not (linked & set(policy.methods) & available):
        return ("Mit dieser Regel könnten Sie sich selbst nicht mehr anmelden: Passwort wäre nicht erlaubt und Sie "
                "haben keinen erlaubten, eingerichteten Anbieter verbunden.")
    blocked = set(policy.required_links) - linked - available
    if blocked:
        names = ", ".join(identities.PROVIDER_LABELS.get(p, p) for p in sorted(blocked))
        return (f"Mit dieser Regel müssten Sie selbst {names} verbinden – dieser Anbieter ist derzeit nicht "
                "eingerichtet, Sie wären bis dahin gesperrt.")
    return None


# =================================================================== Endpunkte
@router.get("/login-policies")
def list_policies(actor: AuthUser = Depends(require(PERM)), db: Session = Depends(get_db)) -> dict:
    """Alle Regeln und die Auswahllisten für die Verwaltungsseite."""
    from schulmanager.server.permissions import ROLE_LABELS

    school = _school()
    classes = school.index("classes")
    rules = db.scalars(select(LoginPolicyRule)).all()
    user_ids = {int(r.scope_ref) for r in rules if r.scope == "user" and r.scope_ref.isdigit()}
    editor_ids = {r.updated_by for r in rules if r.updated_by}
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids | editor_ids)))} if (
        user_ids or editor_ids) else {}
    names = {uid: (u.display_name or u.username) for uid, u in users.items()}
    grades = _grades(school)
    out = [_rule_out(r, classes=classes, users=users, names=names, grades=set(grades)) for r in rules]
    order = {s: i for i, s in enumerate(SCOPES)}
    out.sort(key=lambda r: (order.get(r["scope"], 9), _natural(r["ref"]), AUDIENCES.index(r["audience"])
                            if r["audience"] in AUDIENCES else 9))
    class_counts: dict[str, int] = {}
    for c in school.classes:
        class_counts[str(c.grade)] = class_counts.get(str(c.grade), 0) + 1
    return {
        "rules": out,
        "options": {
            "roles": [{"id": r, "label": ROLE_LABELS.get(r, r), "manageable": r != "admin" or actor.role == "admin"}
                      for r in ROLES],
            "grades": [{"id": g, "label": f"Jahrgang {g}", "classes": class_counts.get(g, 0)} for g in grades],
            "classes": sorted(({"id": c.id, "name": c.name or c.id, "grade": str(c.grade)} for c in school.classes),
                              key=lambda c: _natural(c["name"])),
            "providers": _providers_info(db),
            "methods": [{"id": m, "label": lp.METHOD_LABELS[m]} for m in lp.METHODS],
            "reset_channels": _channels_info(),
            "audiences": [{"id": a, "label": lp.AUDIENCE_LABELS[a]} for a in AUDIENCES],
            "fields": dict(lp.FIELD_LABELS),
        },
        "defaults": lp.DEFAULT_POLICY.public() | {"sources": {f: lp.BUILTIN_SOURCE for f in lp.FIELDS}},
        "can_manage_admins": actor.role == "admin",
    }


def _save(scope: str, ref: str, audience: str | None, body: RuleBody, request: Request, actor: AuthUser,
          db: Session) -> dict:
    ref, audience = _target(db, actor, scope, ref, audience)
    try:
        values = lp.validate_values(body.model_dump())
    except lp.PolicyError as e:
        raise HTTPException(422, str(e)) from e
    key = (scope, ref, audience)
    empty = all(values[name] is None for name in lp.FIELDS)
    reason = _self_lockout(db, actor, key, None if empty else values)
    if reason:
        raise HTTPException(409, reason)
    rule = _find(db, scope, ref, audience)
    before = _values(rule)
    target = f"login_policy:{scope}:{ref or '-'}:{audience}"
    ip = client_ip(request)
    if empty:   # alles „erben“ = keine Regel
        if rule is not None:
            db.delete(rule)
            audit(db, actor, "login_policy.delete", target, {"before": before}, ip=ip)
            db.commit()
            lp.invalidate_cache()
        return {"rule": None}
    if rule is None:
        rule = LoginPolicyRule(scope=scope, scope_ref=ref, audience=audience)
        db.add(rule)
    for name in lp.FIELDS:
        setattr(rule, name, values[name])
    rule.note = body.note.strip()
    rule.updated_at = utcnow()
    rule.updated_by = actor.id or None
    db.flush()
    audit(db, actor, "login_policy.set", target, {"before": before, "after": values, "note": rule.note}, ip=ip)
    db.commit()
    lp.invalidate_cache()
    school = _school()
    users = {}
    if scope == "user":
        u = db.get(User, int(ref))
        users = {u.id: u} if u else {}
    return {"rule": _rule_out(rule, classes=school.index("classes"), users=users,
                              names={actor.id: actor.display_name}, grades=set(_grades(school)))}


def _delete(scope: str, ref: str, audience: str | None, request: Request, actor: AuthUser, db: Session) -> dict:
    ref, audience = _target(db, actor, scope, ref, audience, must_exist=False)
    rule = _find(db, scope, ref, audience)
    if rule is None:
        raise HTTPException(404, "Für diesen Bereich gibt es keine eigene Regel.")
    reason = _self_lockout(db, actor, (scope, ref, audience), None)
    if reason:
        raise HTTPException(409, reason.replace("Mit dieser Regel", "Ohne diese Regel"))
    before = _values(rule)
    db.delete(rule)
    audit(db, actor, "login_policy.delete", f"login_policy:{scope}:{ref or '-'}:{audience}", {"before": before},
          ip=client_ip(request))
    db.commit()
    lp.invalidate_cache()
    return {"ok": True}


@router.put("/login-policies/default")
def put_default(body: RuleBody, request: Request, actor: AuthUser = Depends(require(PERM)),
                db: Session = Depends(get_db)) -> dict:
    return _save("default", "", None, body, request, actor, db)


@router.delete("/login-policies/default")
def delete_default(request: Request, actor: AuthUser = Depends(require(PERM)), db: Session = Depends(get_db)) -> dict:
    return _delete("default", "", None, request, actor, db)


@router.get("/login-policies/effective")
def effective(user_id: Optional[int] = None, class_id: Optional[str] = None, grade: Optional[str] = None,
              role: Optional[str] = None, audience: str = Query("schueler", pattern="^(schueler|eltern)$"),
              actor: AuthUser = Depends(require(PERM)), db: Session = Depends(get_db)) -> dict:
    """„Was gilt für …?“ – Person, Klasse/Jahrgang + Zielgruppe oder Rolle (mit Herkunft je Feld)."""
    school = _school()
    classes = school.index("classes")
    if user_id is not None:
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(404, "Dieses Konto gibt es nicht.")
        policy = lp.effective_policy(db, user)
        inherited = lp.effective_policy(db, user, include_personal=False)
        students = school.index("students")
        sids = [user.student_id] if user.role == "schueler" and user.student_id else (
            list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user.id)))
            if user.role == "eltern" else [])
        members = []
        for sid in sids:
            st = students.get(sid)
            cls = classes.get(st.class_id) if st else None
            members.append({"student_id": sid, "name": st.name if st else sid,
                            "class": {"id": cls.id, "name": cls.name, "grade": str(cls.grade)} if cls else None})
        from schulmanager.server import identities

        linked = sorted(set(identities.linked_providers(db, user.id) or ()))
        decision, _ = lp.password_login(db, user)
        return {"target": {"kind": "user", "user": _person(user), "students": members},
                "policy": policy.public(), "inherited": inherited.public(), "linked": linked,
                "missing_links": lp.missing_links(db, user, policy), "password_login": decision}
    if class_id is not None:
        cls = classes.get(class_id)
        if cls is None:
            raise HTTPException(404, f"Klasse „{class_id}“ gibt es nicht.")
        policy = lp.group_policy(db, class_id=class_id, audience=audience)
        return {"target": {"kind": "class", "class": {"id": cls.id, "name": cls.name, "grade": str(cls.grade)},
                           "audience": audience}, "policy": policy.public()}
    if grade is not None:
        if grade not in _grades(school):
            raise HTTPException(404, f"Jahrgang {grade} gibt es nicht.")
        policy = lp.group_policy(db, grade=grade, audience=audience)
        return {"target": {"kind": "grade", "grade": grade, "audience": audience}, "policy": policy.public()}
    if role is not None:
        if role not in ROLES:
            raise HTTPException(404, f"Unbekannte Rolle „{role}“.")
        return {"target": {"kind": "role", "role": role}, "policy": lp.role_policy(db, role).public()}
    raise HTTPException(422, "Bitte eine Person, Klasse, einen Jahrgang oder eine Rolle angeben.")


@router.get("/login-policies/report")
def report(class_id: str, audience: str = Query("alle", pattern="^(alle|schueler|eltern)$"),
           actor: AuthUser = Depends(require(PERM)), db: Session = Depends(get_db)) -> dict:
    """Wer hat in der Klasse die Pflicht-Verknüpfungen noch nicht hergestellt? (Schüler/innen und/oder Eltern)"""
    from schulmanager.server import identities

    school = _school()
    cls = school.index("classes").get(class_id)
    if cls is None:
        raise HTTPException(404, f"Klasse „{class_id}“ gibt es nicht.")
    students = {s.id: s for s in school.students if s.class_id == class_id}
    accounts: list[tuple[str, Any, User, list[str]]] = []   # (Gruppe, Richtlinien-Sicht, Konto, Schüler-IDs)
    with_account: set[str] = set()
    if audience in ("alle", "schueler") and students:
        for u in db.scalars(select(User).where(User.role == "schueler", User.student_id.in_(list(students)))
                            .order_by(User.display_name, User.username)):
            accounts.append(("schueler", u, u, [u.student_id]))
            with_account.add(u.student_id)
    if audience in ("alle", "eltern") and students:
        links = db.execute(select(ParentLink.parent_user_id, ParentLink.student_id)
                           .where(ParentLink.parent_user_id.in_(select(ParentLink.parent_user_id)
                                                                .where(ParentLink.student_id.in_(list(students)))))
                           .order_by(ParentLink.id)).all()
        children: dict[int, list[str]] = {}
        for pid, sid in links:
            children.setdefault(pid, []).append(sid)
        if children:
            for u in db.scalars(select(User).where(User.id.in_(list(children)), User.role == "eltern")
                                .order_by(User.display_name, User.username)):
                # Eltern-Sicht mit allen Kindern (Vereinigung über die Klassen der Kinder)
                view = SimpleNamespace(id=u.id, role="eltern", student_id=None, student_ids=children[u.id],
                                       must_change_password=u.must_change_password)
                accounts.append(("eltern", view, u, [s for s in children[u.id] if s in students]))
    groups: dict[str, dict[str, Any]] = {g: {"accounts": 0, "required": 0, "complete": 0, "missing": 0}
                                         for g in ("schueler", "eltern")}
    items = []
    for group, acc, row, sids in accounts:
        stats = groups[group]
        stats["accounts"] += 1
        policy = lp.effective_policy(db, acc)
        if not policy.required_links:
            continue
        stats["required"] += 1
        linked = set(identities.linked_providers(db, row.id) or ())
        missing = [p for p in identities.PROVIDERS if p in policy.required_links and p not in linked]
        if not missing:
            stats["complete"] += 1
            continue
        stats["missing"] += 1
        items.append({"user": _person(row), "group": group,
                      "students": [{"id": s, "name": students[s].name} for s in sids if s in students],
                      "required": [p for p in identities.PROVIDERS if p in policy.required_links],
                      "linked": [p for p in identities.PROVIDERS if p in linked], "missing": missing,
                      "last_login": iso(row.last_login)})
    return {"class": {"id": cls.id, "name": cls.name, "grade": str(cls.grade)}, "audience": audience,
            "counts": groups, "students_total": len(students),
            "students_without_account": len(set(students) - with_account) if audience != "eltern" else None,
            "items": items}


@router.put("/login-policies/{scope}/{ref}")
def put_rule(scope: str, ref: str, body: RuleBody, request: Request, audience: Optional[str] = None,
             actor: AuthUser = Depends(require(PERM)), db: Session = Depends(get_db)) -> dict:
    return _save(scope, ref, audience, body, request, actor, db)


@router.delete("/login-policies/{scope}/{ref}")
def delete_rule(scope: str, ref: str, request: Request, audience: Optional[str] = None,
                actor: AuthUser = Depends(require(PERM)), db: Session = Depends(get_db)) -> dict:
    return _delete(scope, ref, audience, request, actor, db)
