"""Anmelde-Richtlinien: wer darf sich wie anmelden (docs/ARCHITECTURE.md §11.5).

VERTRAG (von allen Agenten genutzt, Besitzer: Agent Richtlinien). Die Signaturen bleiben stabil.

* :data:`METHODS` – alle Anmeldewege. ``password`` = Benutzername + Passwort, die übrigen = Anbieter aus
  ``identities.PROVIDERS`` (``oidc`` ist das allgemeine Schulkonto per OpenID Connect).
* :func:`effective_policy` – wirksame Richtlinie eines Kontos (Person > Klasse > Jahrgang > Rolle > Standard).
* :func:`method_allowed` – darf sich ``user`` auf diesem Weg anmelden?

Regeln (Tabelle ``login_policy_rules``, ``feature_models/login_policy.py``) legen je Feld einen Wert fest oder
erben (``NULL``). Vorrang je Feld:

1. Person (``user``),
2. Klasse – erst die Regel der Zielgruppe (``schueler`` bzw. ``eltern``), dann die für ``alle``,
3. Jahrgang – ebenso Zielgruppe vor ``alle``,
4. Rolle, 5. Standard (``default``), 6. eingebaute Voreinstellung (:data:`DEFAULT_POLICY`).

Schüler/innen gehören zur Klasse ihres ``student_id`` (Planungsdokument), Eltern zu den Klassen aller Kinder
(Zielgruppe ``eltern``). Bei mehreren Kindern wird je Kind aufgelöst und vereinigt: Wege, Kanäle und Pflicht-
Verknüpfungen als Vereinigung, Schalter sind wahr, wenn eine Regel wahr ist. Personal kennt nur Person/Rolle/Standard.
Administration: ``password`` ist immer erlaubt (Schutz vor Aussperren), Pflicht-Verknüpfungen gelten nie.

Die Regeln werden prozessweit :data:`CACHE_SECONDS` zwischengespeichert (``deps`` braucht sie bei jeder Anfrage);
Schreiben über die ORM-Sitzung leert den Speicher nach dem Commit automatisch, sonst :func:`invalidate_cache`.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

log = logging.getLogger("schulmanager.login_policy")

METHODS: tuple[str, ...] = ("password", "microsoft", "apple", "google", "oidc")
RESET_CHANNELS: tuple[str, ...] = ("email", "sms")
FIELDS: tuple[str, ...] = ("methods", "required_links", "self_link", "reset_channels", "sso_create")
LIST_FIELDS: tuple[str, ...] = ("methods", "required_links", "reset_channels")
BOOL_FIELDS: tuple[str, ...] = ("self_link", "sso_create")

METHOD_LABELS: dict[str, str] = {"password": "Passwort", "microsoft": "Microsoft", "apple": "Apple",
                                 "google": "Google", "oidc": "Schulkonto"}
CHANNEL_LABELS: dict[str, str] = {"email": "E-Mail", "sms": "SMS"}
AUDIENCE_LABELS: dict[str, str] = {"alle": "Alle", "schueler": "Schüler/innen", "eltern": "Eltern"}
FIELD_LABELS: dict[str, str] = {"methods": "Anmeldewege", "required_links": "Pflicht-Verknüpfungen",
                                "self_link": "Konten selbst verbinden/trennen",
                                "reset_channels": "Passwort vergessen per",
                                "sso_create": "Beim ersten Anbieter-Login per E-Mail zuordnen"}

BUILTIN_SOURCE = "Voreinstellung"
DEFAULT_SOURCE = "Standard"
PERSON_SOURCE = "Person"
ADMIN_PASSWORD_NOTE = "Passwort für die Administration immer erlaubt"
ADMIN_LINKS_SOURCE = "Administration: keine Pflicht-Verknüpfungen"
CACHE_SECONDS = 5.0


@dataclass(frozen=True)
class EffectivePolicy:
    methods: frozenset[str] = frozenset(METHODS)          # erlaubte Anmeldewege
    required_links: frozenset[str] = frozenset()          # Anbieter, die verbunden sein MÜSSEN
    self_link: bool = True                                # darf eigene Anbieter-Konten verbinden/trennen
    reset_channels: frozenset[str] = frozenset(RESET_CHANNELS)  # „Passwort vergessen“ über diese Wege
    sso_create: bool = False                              # beim ersten Anbieter-Login per bestätigter E-Mail zuordnen
    sources: dict[str, str] = field(default_factory=dict)  # Feld → Herkunft, z. B. {"methods": "Klasse 5a · Schüler/innen"}

    def public(self) -> dict[str, Any]:
        return {"methods": _ordered(self.methods, METHODS), "required_links": _ordered(self.required_links, _providers()),
                "self_link": self.self_link, "reset_channels": _ordered(self.reset_channels, RESET_CHANNELS),
                "sso_create": self.sso_create, "sources": dict(self.sources)}


DEFAULT_POLICY = EffectivePolicy()


class PolicyError(ValueError):
    """Ungültige Regel (deutscher Text für die Antwort 422)."""


# =========================================================================== Hilfen
def _providers() -> tuple[str, ...]:
    from . import identities

    return tuple(identities.PROVIDERS)


def _ordered(values: Iterable[str], order: Iterable[str]) -> list[str]:
    """Werte in fester Reihenfolge (bekannte zuerst), unbekannte alphabetisch dahinter."""
    vals = set(values)
    order = list(order)
    return [v for v in order if v in vals] + sorted(vals - set(order))


def _builtin(name: str) -> Any:
    return getattr(DEFAULT_POLICY, name)


def role_label(role: str) -> str:
    from .permissions import ROLE_LABELS

    return ROLE_LABELS.get(role, role)


def _with_audience(label: str, audience: str) -> str:
    return label if audience == "alle" else f"{label} · {AUDIENCE_LABELS.get(audience, audience)}"


def scope_label(scope: str, ref: str, audience: str = "alle", *, class_name: str | None = None,
                person: str | None = None) -> str:
    """Lesbare Herkunft einer Regel, z. B. „Klasse 5a · Schüler/innen“, „Jahrgang 7“, „Rolle Eltern“, „Standard“."""
    if scope == "default":
        return DEFAULT_SOURCE
    if scope == "role":
        return f"Rolle {role_label(ref)}"
    if scope == "grade":
        return _with_audience(f"Jahrgang {ref}", audience)
    if scope == "class":
        return _with_audience(f"Klasse {class_name or ref}", audience)
    if scope == "user":
        return f"{PERSON_SOURCE} {person}" if person else PERSON_SOURCE
    return f"{scope} {ref}".strip()


# =========================================================================== Regeln laden (mit Cache)
_lock = threading.Lock()
_generation = 0
_cache: dict[str, Any] = {"key": None, "at": 0.0, "rules": {}}

RuleKey = tuple[str, str, str]   # (scope, scope_ref, audience)


def invalidate_cache() -> None:
    """Zwischenspeicher der Regeln verwerfen (nach dem Commit einer Änderung)."""
    global _generation
    with _lock:
        _generation += 1
        _cache.update(key=None, at=0.0, rules={})


def _bind_key(db) -> tuple:
    bind = db.get_bind()
    return id(bind), str(getattr(bind, "url", ""))


def _clean_list(name: str, value: Any) -> list[str] | None:
    """Gespeicherte Liste auf bekannte Werte begrenzen; leere ``methods`` gelten als „erben“ (nie aussperren)."""
    if value is None or not isinstance(value, (list, tuple)):
        return None
    allowed = {"methods": METHODS, "required_links": _providers(), "reset_channels": RESET_CHANNELS}[name]
    out = [v for v in allowed if v in set(value)]
    if name == "methods" and not out:
        return None
    return out


def _row_values(row) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in LIST_FIELDS:
        values[name] = _clean_list(name, getattr(row, name))
    for name in BOOL_FIELDS:
        value = getattr(row, name)
        values[name] = None if value is None else bool(value)
    return values


def load_rules(db) -> dict[RuleKey, dict[str, Any]]:
    """Alle Regeln ``(scope, scope_ref, audience) → {feld: wert|None}`` (prozessweit kurz zwischengespeichert).

    Gelesen wird in einer eigenen Sitzung auf derselben Datenbank – ein Fehler hier stört die Transaktion des
    Aufrufers nicht (dann gilt die Voreinstellung, mit Log-Eintrag).
    """
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    from .feature_models.login_policy import LoginPolicyRule

    key = _bind_key(db)
    now = time.monotonic()
    with _lock:
        if _cache["key"] == key and now - _cache["at"] < CACHE_SECONDS:
            return _cache["rules"]
        generation = _generation
    try:
        with Session(bind=db.get_bind()) as session:
            rows = session.scalars(select(LoginPolicyRule)).all()
            rules = {(r.scope, r.scope_ref or "", r.audience or "alle"): _row_values(r) for r in rows}
    except SQLAlchemyError:
        log.exception("Anmelde-Richtlinien konnten nicht gelesen werden – es gilt die Voreinstellung")
        rules = {}
    with _lock:
        if generation == _generation:
            _cache.update(key=key, at=now, rules=rules)
    return rules


# =========================================================================== Zugehörigkeit (Klasse, Jahrgang)
_school_cache: dict[str, Any] = {"key": None, "students": {}, "classes": {}}


def _school_maps() -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """``student_id → class_id`` und ``class_id → (Name, Jahrgang als Text)`` aus dem Planungsdokument."""
    from .store import get_store

    store = get_store()
    school = store.school
    key = (id(school), store.version)
    with _lock:
        if _school_cache["key"] == key:
            return _school_cache["students"], _school_cache["classes"]
    students = {s.id: s.class_id for s in school.students}
    classes = {c.id: (c.name or c.id, str(c.grade)) for c in school.classes}
    with _lock:
        _school_cache.update(key=key, students=students, classes=classes)
    return students, classes


Level = tuple[RuleKey, str]   # (Regel-Schlüssel, Herkunftstext)
ClassMaps = dict[str, tuple[str, str]]


def _class_refs(class_id: str | None, grade: str | None, classes: ClassMaps) -> list[tuple[str, str]]:
    if class_id is None:
        return []
    return [(class_id, f"Klasse {classes.get(class_id, (class_id, ''))[0]}")]


def _grade_refs(class_id: str | None, grade: str | None, classes: ClassMaps) -> list[tuple[str, str]]:
    if grade is None and class_id is not None and class_id in classes:
        grade = classes[class_id][1]
    return [(grade, f"Jahrgang {grade}")] if grade is not None else []


# Gruppen-Bereiche einer Klasse in Vorrang-Reihenfolge: (scope, Funktion → [(scope_ref, Herkunft)]).
# Erweiterbar: ein späterer Bereich ``group`` (Klassengruppen wie „IT-Zweig 11–13“) liefert hier alle Gruppen
# der Klasse und wird zwischen ``class`` und ``grade`` eingefügt (+ ``AUDIENCE_SCOPES`` im Modell, Validierung).
MEMBER_SCOPES: tuple[tuple[str, Callable[[str | None, str | None, ClassMaps], list[tuple[str, str]]]], ...] = (
    ("class", _class_refs),
    ("grade", _grade_refs),
)


def group_levels(class_id: str | None = None, audience: str = "schueler", *,
                 grade: str | None = None) -> list[Level]:
    """Stufen einer Zielgruppe (Klasse, Jahrgang …) – je Bereich die Zielgruppe vor „alle“."""
    _, classes = _school_maps()
    audiences = (audience, "alle") if audience != "alle" else ("alle",)
    levels: list[Level] = []
    for scope, refs in MEMBER_SCOPES:
        for ref, label in refs(class_id, grade, classes):
            for aud in audiences:
                levels.append(((scope, ref, aud), _with_audience(label, aud)))
    return levels


def _member_levels(student_id: str | None, audience: str) -> list[Level]:
    if not student_id:
        return []
    students, _ = _school_maps()
    class_id = students.get(student_id)
    return group_levels(class_id, audience) if class_id else []


def _role_levels(role: str) -> list[Level]:
    return [(("role", role, "alle"), scope_label("role", role)), (("default", "", "alle"), DEFAULT_SOURCE)]


def _child_ids(db, user) -> list[str]:
    ids = getattr(user, "student_ids", None)
    if ids is None:   # ORM-User: Kinder aus ParentLink
        from sqlalchemy import select

        from .db_models import ParentLink

        ids = list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user.id)
                              .order_by(ParentLink.id)))
    return list(dict.fromkeys(ids))


# =========================================================================== Auflösung
def _pick(rules: dict, chain: list[Level], name: str) -> tuple[Any, str] | None:
    for key, label in chain:
        rule = rules.get(key)
        if rule is not None and rule.get(name) is not None:
            return rule[name], label
    return None


def _combine(name: str, picks: list[tuple[Any, str]]) -> tuple[Any, str]:
    """Mehrere Kinder: Listen vereinigen, Schalter wahr, wenn einer wahr ist; Herkunft = beitragende Regeln."""
    if len(picks) == 1:
        return picks[0]
    if name in BOOL_FIELDS:
        value = any(v for v, _ in picks)
        labels = [label for v, label in picks if bool(v) == value]
    else:
        merged: set[str] = set()
        for v, _ in picks:
            merged |= set(v)
        value = list(merged)
        labels = [label for v, label in picks if v] or [label for _, label in picks]
    return value, " + ".join(dict.fromkeys(labels))


def resolve(db, *, role: str, head: list[Level] | None = None, groups: list[list[Level]] | None = None,
            rules: dict | None = None) -> EffectivePolicy:
    """Löst die Felder über ``head`` (Person) → je Gruppe (Klasse/Jahrgang) → Rolle → Standard auf.

    ``groups`` = eine Liste je Zugehörigkeit (Schüler/in: eine, Eltern: je Kind, Personal: ``[[]]``).
    """
    rules = load_rules(db) if rules is None else rules
    head = head or []
    groups = groups or [[]]
    tail = _role_levels(role)
    values: dict[str, Any] = {}
    sources: dict[str, str] = {}
    for name in FIELDS:
        got = _pick(rules, head, name)
        if got is None:
            picks = [_pick(rules, group + tail, name) or (_builtin(name), BUILTIN_SOURCE) for group in groups]
            got = _combine(name, picks)
        values[name], sources[name] = got
    methods = frozenset(values["methods"])
    required = frozenset(values["required_links"])
    if role == "admin":   # Aussperr-Schutz: Passwort immer, keine Pflicht-Verknüpfungen
        if "password" not in methods:
            methods = methods | {"password"}
            sources["methods"] = f"{sources['methods']} · {ADMIN_PASSWORD_NOTE}"
        if required:
            required = frozenset()
            sources["required_links"] = ADMIN_LINKS_SOURCE
    return EffectivePolicy(methods=methods, required_links=required, self_link=bool(values["self_link"]),
                           reset_channels=frozenset(values["reset_channels"]),
                           sso_create=bool(values["sso_create"]), sources=sources)


def effective_policy(db, user, *, include_personal: bool = True, rules: dict | None = None) -> EffectivePolicy:
    """Wirksame Richtlinie für ``user`` (``db_models.User`` oder ``deps.AuthUser``).

    ``include_personal=False`` lässt die Personen-Regel weg (Anzeige „erbt“ im Regel-Editor); ``rules`` ersetzt
    die gespeicherten Regeln (Probe vor dem Speichern).
    """
    role = getattr(user, "role", "") or ""
    uid = getattr(user, "id", None)
    head: list[Level] = []
    if include_personal and uid:
        head = [(("user", str(uid), "alle"), PERSON_SOURCE)]
    if role == "schueler":
        groups = [_member_levels(getattr(user, "student_id", None), "schueler")]
    elif role == "eltern":
        groups = [_member_levels(sid, "eltern") for sid in _child_ids(db, user)] or [[]]
    else:
        groups = [[]]
    return resolve(db, role=role, head=head, groups=groups, rules=rules)


def method_allowed(db, user, method: str) -> bool:
    return method in effective_policy(db, user).methods


def group_policy(db, *, class_id: str | None = None, grade: str | None = None,
                 audience: str = "schueler") -> EffectivePolicy:
    """Vorschau: Richtlinie eines (gedachten) Mitglieds der Klasse bzw. des Jahrgangs (Zielgruppe schueler|eltern)."""
    role = "eltern" if audience == "eltern" else "schueler"
    return resolve(db, role=role, groups=[group_levels(class_id, role, grade=grade)])


def role_policy(db, role: str) -> EffectivePolicy:
    """Vorschau: Richtlinie eines Kontos der Rolle ohne Klassen-/Personen-Regeln."""
    return resolve(db, role=role)


# =========================================================================== Ersteinrichtung / Pflicht-Verknüpfungen
def missing_links(db, user, policy: EffectivePolicy | None = None) -> list[str]:
    """Pflicht-Anbieter, die ``user`` noch nicht verbunden hat (Reihenfolge wie ``identities.PROVIDERS``)."""
    policy = policy or effective_policy(db, user)
    if not policy.required_links:
        return []
    from . import identities

    linked = set(identities.linked_providers(db, int(user.id)) or ())
    return _ordered(set(policy.required_links) - linked, _providers())


def available_provider_ids(db) -> set[str]:
    from . import identities

    out: set[str] = set()
    for item in identities.available_providers(db) or []:
        pid = item.get("id") if isinstance(item, dict) else item
        if pid:
            out.add(str(pid))
    return out


def password_login(db, user) -> tuple[str, EffectivePolicy]:
    """Entscheidung für eine Passwort-Anmeldung mit **bereits geprüftem** Passwort.

    ``"ok"`` – Passwort ist erlaubt; ``"setup"`` – Ersteinrichtung (Startpasswort + fehlende Pflicht-Verknüpfung,
    die über einen verfügbaren Anbieter herstellbar ist): Sitzung nur zum Verbinden; ``"denied"`` – nicht erlaubt.
    Die Ersteinrichtung gilt nur, solange das Konto noch keinen erlaubten, verfügbaren Anbieter verbunden hat – kommt
    später eine weitere Pflicht-Verknüpfung hinzu, meldet man sich über den Anbieter an (``link_required``), nicht
    erneut mit dem (womöglich weitergegebenen) Startpasswort.
    """
    policy = effective_policy(db, user)
    if "password" in policy.methods:
        return "ok", policy
    if getattr(user, "must_change_password", False) and policy.required_links:
        from . import identities

        linked = set(identities.linked_providers(db, int(user.id)) or ())
        available = available_provider_ids(db)
        missing = set(policy.required_links) - linked
        if missing & available and not (linked & set(policy.methods) & available):
            return "setup", policy
    return "denied", policy


def login_methods_hint(policy: EffectivePolicy) -> list[str]:
    """Erlaubte Wege außer Passwort (für den Hinweis der Login-Seite)."""
    return [m for m in _ordered(policy.methods, METHODS) if m != "password"]


# =========================================================================== Regeln prüfen
def validate_values(values: dict[str, Any]) -> dict[str, Any]:
    """Prüft und normalisiert die Felder einer Regel (``None`` = erben). Wirft :class:`PolicyError`."""
    out: dict[str, Any] = {}
    allowed = {"methods": (METHODS, METHOD_LABELS, "Unbekannter Anmeldeweg"),
               "required_links": (_providers(), None, "Unbekannter Anbieter"),
               "reset_channels": (RESET_CHANNELS, CHANNEL_LABELS, "Unbekannter Kanal")}
    for name in LIST_FIELDS:
        value = values.get(name)
        if value is None:
            out[name] = None
            continue
        if isinstance(value, str) or not isinstance(value, (list, tuple, set, frozenset)):
            raise PolicyError(f"{FIELD_LABELS[name]}: Liste erwartet.")
        options, _labels, message = allowed[name]
        unknown = sorted({str(v) for v in value} - set(options))
        if unknown:
            raise PolicyError(f"{message}: {', '.join(unknown)}.")
        out[name] = [o for o in options if o in set(value)]
    if out["methods"] is not None and not out["methods"]:
        raise PolicyError("Mindestens ein Anmeldeweg muss erlaubt sein – sonst kann sich niemand mehr anmelden.")
    for name in BOOL_FIELDS:
        value = values.get(name)
        if value is not None and not isinstance(value, bool):
            raise PolicyError(f"{FIELD_LABELS[name]}: Ja/Nein erwartet.")
        out[name] = value
    return out
