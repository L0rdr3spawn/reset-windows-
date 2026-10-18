"""Schuljahreswechsel-Assistent (``docs/PRODUKTREIFE.md``, Hilfe: ``docs/hilfe/schulleitung.md``).

Ablauf: **Vorschau** (:func:`preview`, ändert nichts) → **Ausführen** (:func:`execute`, nur mit dem Token der Vorschau,
d. h. nur für genau diese Planung und diesen Stand des Plans) → bei Bedarf **Rückgängig** (:func:`undo`).

Was der Wechsel tut (alles einzeln abwählbar):

* Klassen hochstufen: Jahrgang +1, Klassenname mit führender Jahrgangszahl wird mitgezogen („5a“ → „6a“); die interne
  Klassen-ID bleibt. Pro Klasse überschreibbar: ``promote`` | ``graduate`` | ``keep`` (z. B. jahrgangsgemischte Gruppen).
* Abgänger: Klassen ab ``final_grade`` (Standard: höchster Jahrgang) und ``extra_leavers`` (einzelne Schüler/innen)
  verlassen das Planungsdokument (samt Kursen/Stunden, die nur diese Klassen hatten). Die Konten (Schüler/in und
  Eltern ohne weiteres Kind an der Schule) werden **gesperrt** und abgemeldet – nicht gelöscht. Die endgültige Löschung
  übernimmt das Löschkonzept (``docs/DATENSCHUTZ-LOESCHKONZEPT.md``); dafür gibt es die Schnittstelle
  :func:`register_leaver_handler` (Handler bekommen ``LeaverBatch``).
* Neue Klassen (Schulanfänger/Eingangsstufe) anlegen – die Schüler/innen danach per CSV importieren.
* Kursräume archivieren (nur gelöschter Kurse/Klassen oder alle), Notenbücher abschließen (sperren).
* Neues Schuljahr: Beginn setzen, alter Beginn in ``school_year_history``; optional Stundenplan leeren.

Rückgängig: nur solange der Plan seit dem Wechsel nicht weiter geändert wurde (sonst Verlauf nutzen): Planungsdokument
auf die Version vor dem Wechsel, gesperrte Konten wieder frei, archivierte Kursräume wieder offen, Notenbücher wieder
geöffnet. Abgemeldete Sitzungen kommen nicht zurück.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from . import ops
from .config import config
from .db import iso, session_scope, utcnow
from .db_models import ParentLink, User

log = logging.getLogger("schulmanager.year_change")

STATE_KEY = "yearchange"
KEEP_RUNS = 5


# ---------------------------------------------------------------------------
# Eingabe
# ---------------------------------------------------------------------------
class ClassRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["promote", "graduate", "keep"]


class NewClass(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=40)
    grade: int = Field(ge=1, le=13)
    site: str = Field("", max_length=40)
    count: int = Field(25, ge=0, le=60)


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_year_start: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    final_grade: Optional[int] = Field(None, ge=1, le=13)
    class_rules: dict[str, ClassRule] = Field(default_factory=dict, max_length=500)
    extra_leavers: list[str] = Field(default_factory=list, max_length=5000)
    rename_classes: bool = True
    new_classes: list[NewClass] = Field(default_factory=list, max_length=100)
    archive_rooms: Literal["none", "removed", "all"] = "removed"
    lock_gradebooks: bool = True
    deactivate_accounts: bool = True
    clear_lessons: bool = False


@dataclass
class LeaverBatch:
    """Übergabe an die Handler (Löschkonzept): wer die Schule verlässt und welche Konten gesperrt wurden."""
    student_ids: list[str]
    user_ids: list[int]
    school_year_end: str
    reason: str = "schuljahreswechsel"
    extra: dict[str, Any] = field(default_factory=dict)


LeaverHandler = Callable[[Any, LeaverBatch, Any], Optional[dict]]
_handlers: list[LeaverHandler] = []


def register_leaver_handler(fn: LeaverHandler) -> None:
    """Schnittstelle für das Löschkonzept: ``fn(db, batch, user)`` wird nach dem Sperren der Konten aufgerufen
    (gleiche Transaktion; Rückgabe optional als Hinweistext-Dict, landet im Protokoll des Laufs)."""
    if fn not in _handlers:
        _handlers.append(fn)


def clear_leaver_handlers() -> None:
    _handlers.clear()


# ---------------------------------------------------------------------------
# Berechnung
# ---------------------------------------------------------------------------
def _parse(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(422, "Ungültiges Datum für den Beginn des neuen Schuljahres") from None


def year_label(start: date) -> str:
    return f"{start.year}/{str(start.year + 1)[2:]}"


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "", name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
               .replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue").replace("ß", "ss"))
    return s[:30] or "Klasse"


def promoted_name(name: str, grade: int) -> str:
    """„5a“ (Jahrgang 5) → „6a“; Namen ohne passende führende Zahl bleiben."""
    m = re.match(r"^(\d{1,2})(.*)$", name)
    if m and int(m.group(1)) == grade:
        return f"{grade + 1}{m.group(2)}"
    return name


def _current_start(school) -> Optional[date]:
    from .. import calendar_utils as cu

    st = school.settings
    if not (st.school_year_start or st.cycle_start):
        return None
    try:
        return cu.base_start(st)
    except Exception:  # noqa: BLE001
        return None


def compute(school, plan: Plan) -> dict[str, Any]:
    """Was würde passieren? Reine Berechnung auf dem Dokument (ohne Datenbank)."""
    new_start = _parse(plan.new_year_start)
    old_start = _current_start(school)
    warnings: list[str] = []
    conflicts: list[str] = []
    if old_start is not None and new_start <= old_start:
        conflicts.append("Der neue Schuljahresbeginn muss nach dem bisherigen Beginn "
                         f"({old_start.strftime('%d.%m.%Y')}) liegen.")
    elif old_start is not None and (new_start - old_start).days < 200:
        warnings.append("Der neue Beginn liegt weniger als 200 Tage nach dem bisherigen – ist das wirklich ein "
                        "neues Schuljahr?")
    grades = [c.grade for c in school.classes]
    final_grade = plan.final_grade or (max(grades) if grades else 0)
    counts: dict[str, int] = {}
    for s in school.students:
        counts[s.class_id] = counts.get(s.class_id, 0) + 1
    index = school.index("students")
    classes = []
    for c in sorted(school.classes, key=lambda x: (x.grade, x.name)):
        rule = plan.class_rules.get(c.id)
        action = rule.action if rule else ("graduate" if final_grade and c.grade >= final_grade else "promote")
        new_name, new_grade = c.name, c.grade
        if action == "promote":
            new_grade = c.grade + 1
            if plan.rename_classes:
                new_name = promoted_name(c.name, c.grade)
        classes.append({"id": c.id, "name": c.name, "grade": c.grade, "action": action, "new_name": new_name,
                        "new_grade": new_grade, "students": counts.get(c.id, 0)})
    for rid in plan.class_rules:
        if rid not in school.index("classes"):
            conflicts.append(f"Klasse {rid} aus den Vorgaben gibt es nicht.")
    leaving_classes = {c["id"] for c in classes if c["action"] == "graduate"}
    leavers: dict[str, str] = {s.id: s.class_id for s in school.students if s.class_id in leaving_classes}
    for sid in plan.extra_leavers:
        if sid not in index:
            conflicts.append(f"Schüler/in {sid} gibt es nicht.")
        else:
            leavers.setdefault(sid, index[sid].class_id)
    # doppelte Klassennamen nach dem Wechsel
    seen: dict[str, str] = {}
    final_names = [(c["new_name"], c["id"]) for c in classes if c["action"] != "graduate"]
    final_names += [(n.name, "(neu)") for n in plan.new_classes]
    for name, cid in final_names:
        key = name.strip().lower()
        if key in seen:
            conflicts.append(f"Der Klassenname „{name}“ würde doppelt vergeben ({seen[key]} und {cid}).")
        seen[key] = cid
    new_ids = {c.id for c in school.classes}
    for n in plan.new_classes:
        base = _slug(n.name)
        if base in new_ids and base not in leaving_classes:
            conflicts.append(f"Für die neue Klasse „{n.name}“ gibt es bereits die Kennung {base}.")
    removed_courses = _courses_without_classes(school, leaving_classes)
    lessons_removed = sum(1 for le in school.lessons if le.course_id in removed_courses)
    if plan.clear_lessons:
        warnings.append("Der Stundenplan wird geleert – danach muss ein neuer Plan erzeugt werden.")
    else:
        warnings.append("Der Stundenplan bleibt unverändert. Nach dem Wechsel Kurse und Stundenplan für das neue "
                        "Schuljahr prüfen bzw. neu erzeugen.")
    if not plan.new_classes and leaving_classes:
        warnings.append("Es sind keine neuen Eingangsklassen vorgesehen – sollen Schulanfänger/innen ergänzt werden?")
    if any(c.class_teacher for c in school.classes if c.id in leaving_classes):
        warnings.append("Klassenleitungen abgehender Klassen werden frei.")
    return {
        "old_year": year_label(old_start) if old_start else "",
        "new_year": year_label(new_start), "old_start": old_start.isoformat() if old_start else "",
        "new_start": new_start.isoformat(), "final_grade": final_grade, "classes": classes,
        "leavers": {"count": len(leavers), "by_class": _group(leavers),
                    "sample": [{"id": sid, "name": index[sid].name, "class_id": cid}
                               for sid, cid in list(leavers.items())[:15] if sid in index]},
        "courses_removed": len(removed_courses), "lessons_removed": lessons_removed,
        "new_classes": [{"name": n.name, "grade": n.grade, "count": n.count} for n in plan.new_classes],
        "warnings": warnings, "conflicts": conflicts, "leaver_ids": list(leavers),
    }


def _group(leavers: dict[str, str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for cid in leavers.values():
        out[cid] = out.get(cid, 0) + 1
    return out


def _courses_without_classes(school, leaving: set[str]) -> set[str]:
    return {c.id for c in school.courses if c.classes and all(x in leaving for x in c.classes)}


def _digest(school_digest: str, plan: Plan) -> str:
    payload = school_digest + "|" + json.dumps(plan.model_dump(), sort_keys=True, ensure_ascii=False)
    return hmac.new(config.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _db_effects(db, school, plan: Plan, info: dict) -> dict[str, Any]:
    """Teil der Vorschau, der die Datenbank betrifft (Konten, Kursräume, Notenbücher) – nur zählen."""
    from .feature_models.channels import Channel
    from .feature_models.gradebook import GradeBook

    leaver_ids = set(info["leaver_ids"])
    users, parents = _accounts_of(db, school, leaver_ids)
    leaving_classes = {c["id"] for c in info["classes"] if c["action"] == "graduate"}
    removed_courses = _courses_without_classes(school, leaving_classes)
    channels = _channels_to_archive(db, school, plan, leaving_classes, removed_courses)
    books = [b.id for b in db.scalars(select(GradeBook).where(GradeBook.locked_at.is_(None))).all()] \
        if plan.lock_gradebooks else []
    return {"student_accounts": len(users), "parent_accounts": len(parents), "rooms": len(channels),
            "gradebooks": len(books), "_users": users + parents, "_channels": channels, "_books": books,
            "_channel_model": Channel}


def _accounts_of(db, school, leaver_ids: set[str]) -> tuple[list[int], list[int]]:
    if not leaver_ids:
        return [], []
    remaining = {s.id for s in school.students} - leaver_ids
    students = [u.id for u in db.scalars(select(User).where(User.student_id.in_(leaver_ids), User.role == "schueler",
                                                            User.active.is_(True))).all()]
    links = db.execute(select(ParentLink.parent_user_id, ParentLink.student_id)).all()
    by_parent: dict[int, set[str]] = {}
    for pid, sid in links:
        by_parent.setdefault(pid, set()).add(sid)
    parent_ids = [pid for pid, sids in by_parent.items() if sids & leaver_ids and not (sids & remaining)]
    parents = [u.id for u in db.scalars(select(User).where(User.id.in_(parent_ids), User.role == "eltern",
                                                           User.active.is_(True))).all()] if parent_ids else []
    return students, parents


def _channels_to_archive(db, school, plan: Plan, leaving_classes: set[str], removed_courses: set[str]) -> list[int]:
    from .feature_models.channels import Channel

    if plan.archive_rooms == "none":
        return []
    rows = db.scalars(select(Channel).where(Channel.archived.is_(False))).all()
    out = []
    for ch in rows:
        if ch.kind == "custom":
            continue
        if plan.archive_rooms == "all":
            out.append(ch.id)
        elif ch.kind == "class" and ch.ref in leaving_classes:
            out.append(ch.id)
        elif ch.kind == "course" and (ch.ref or "").split("#", 1)[0] in removed_courses:
            out.append(ch.id)
    return out


def preview(plan: Plan) -> dict[str, Any]:
    from .store import get_store

    store = get_store()
    school = store.school
    info = compute(school, plan)
    with session_scope() as db:
        eff = _db_effects(db, school, plan, info)
    info.pop("leaver_ids")
    info["accounts"] = {"students": eff["student_accounts"], "parents": eff["parent_accounts"]}
    info["rooms"] = eff["rooms"]
    info["gradebooks"] = eff["gradebooks"]
    info["token"] = _digest(store.digest, plan)
    info["base_version"] = store.version
    info["can_execute"] = not info["conflicts"]
    return info


# ---------------------------------------------------------------------------
# Ausführen
# ---------------------------------------------------------------------------
def _apply_to_school(school, plan: Plan, info: dict) -> None:
    from ..models import SchoolClass
    from .routes.features_data import cascade_delete

    classes = {c.id: c for c in school.classes}
    leaving = {c["id"] for c in info["classes"] if c["action"] == "graduate"}
    for cid in leaving:
        cascade_delete(school, "classes", cid)
    school.classes = [c for c in school.classes if c.id not in leaving]
    gone_students = set(info["leaver_ids"])
    for sid in gone_students:
        cascade_delete(school, "students", sid)
    school.students = [s for s in school.students if s.id not in gone_students]
    for row in info["classes"]:
        if row["action"] == "promote":
            c = classes[row["id"]]
            c.grade, c.name = row["new_grade"], row["new_name"]
    used = {c.id for c in school.classes}
    for n in plan.new_classes:
        cid, k = _slug(n.name), 2
        while cid in used:
            cid, k = f"{_slug(n.name)}{k}", k + 1
        used.add(cid)
        school.classes.append(SchoolClass(id=cid, name=n.name.strip(), grade=n.grade, students=n.count,
                                          site=n.site))
    st = school.settings
    old = _current_start(school)
    if old is not None:
        st.school_year_history = sorted(set(st.school_year_history) | {old.isoformat()})[-20:]
    st.school_year_start = info["new_start"]
    if old is not None:        # Planzeiträume ziehen mit dem neuen Schuljahr mit (gleiche Wochen, neue Daten)
        from schulmanager.calendar_utils import monday_of
        from schulmanager.plan_periods import shift_dates
        shift_dates(school, (monday_of(date.fromisoformat(info["new_start"])) - monday_of(old)).days)
    if plan.clear_lessons:
        school.lessons = []
        school.overrides = []


def execute(plan: Plan, token: str, user: Any, ip: str | None = None) -> dict[str, Any]:
    from .audit import audit
    from .store import get_store

    store = get_store()
    if not hmac.compare_digest(token or "", _digest(store.digest, plan)):
        raise HTTPException(409, "Der Plan hat sich seit der Vorschau geändert oder die Vorgaben wurden angepasst – "
                                 "bitte die Vorschau neu erstellen.")
    info = compute(store.school, plan)
    if info["conflicts"]:
        raise HTTPException(422, "; ".join(info["conflicts"]))
    before_version = store.version
    with session_scope() as db:
        eff = _db_effects(db, store.school, plan, info)
    store.mutate(user, f"Schuljahreswechsel auf {info['new_year']}", lambda s: _apply_to_school(s, plan, info),
                 scope=["all"])
    after_version = store.version
    journal: dict[str, Any] = {"users": [], "channels": [], "books": []}
    notes: list[str] = []
    try:
        with session_scope() as db:
            if plan.deactivate_accounts and eff["_users"]:
                from .accounts import revoke_sessions

                for u in db.scalars(select(User).where(User.id.in_(eff["_users"]), User.active.is_(True))).all():
                    u.active = False
                    revoke_sessions(db, u.id)
                    journal["users"].append(u.id)
            if eff["_channels"]:
                Channel = eff["_channel_model"]
                for ch in db.scalars(select(Channel).where(Channel.id.in_(eff["_channels"]))).all():
                    ch.archived = True
                    journal["channels"].append(ch.id)
            if eff["_books"]:
                from .feature_models.gradebook import GradeBook

                now = utcnow()
                for b in db.scalars(select(GradeBook).where(GradeBook.id.in_(eff["_books"]),
                                                            GradeBook.locked_at.is_(None))).all():
                    b.locked_at, b.locked_by = now, getattr(user, "id", None) or None
                    b.locked_by_name = getattr(user, "display_name", "") or "Schuljahreswechsel"
                    journal["books"].append(b.id)
            batch = LeaverBatch(student_ids=list(info["leaver_ids"]), user_ids=list(journal["users"]),
                                school_year_end=info["old_year"])
            if batch.student_ids:
                for handler in list(_handlers):
                    try:
                        res = handler(db, batch, user)
                        if res:
                            notes.append(str(res)[:200])
                    except Exception:  # noqa: BLE001 - Löschkonzept-Handler dürfen den Wechsel nicht kippen
                        log.exception("Handler für Abgänger fehlgeschlagen")
                        notes.append("Ein Handler des Löschkonzepts ist fehlgeschlagen – siehe Fehlerprotokoll.")
            audit(db, user, "yearchange.execute", info["new_year"],
                  {"classes": len(info["classes"]), "leavers": info["leavers"]["count"],
                   "users": len(journal["users"]), "rooms": len(journal["channels"]),
                   "gradebooks": len(journal["books"]), "base_version": before_version}, ip=ip)
    except Exception:
        # Planungsdokument zurückholen, damit nichts halb geändert bleibt
        log.exception("Schuljahreswechsel: Datenbankteil fehlgeschlagen – Planung wird zurückgesetzt")
        store.restore(user, before_version)
        raise HTTPException(500, "Der Schuljahreswechsel ist fehlgeschlagen und wurde zurückgenommen.") from None
    run = {"id": hashlib.sha1(f"{before_version}:{after_version}:{iso(utcnow())}".encode()).hexdigest()[:10],
           "at": iso(utcnow()), "by": getattr(user, "username", ""), "old_year": info["old_year"],
           "new_year": info["new_year"], "before_version": before_version, "after_version": store.version,
           "summary": {"promoted": sum(1 for c in info["classes"] if c["action"] == "promote"),
                       "graduated": sum(1 for c in info["classes"] if c["action"] == "graduate"),
                       "leavers": info["leavers"]["count"], "new_classes": len(plan.new_classes),
                       "accounts": len(journal["users"]), "rooms": len(journal["channels"]),
                       "gradebooks": len(journal["books"])},
           "journal": journal, "undone_at": None, "notes": notes}
    state = ops.get_state(STATE_KEY) or {}
    runs = ([run] + list(state.get("runs") or []))[:KEEP_RUNS]
    ops.set_state(STATE_KEY, {"runs": runs}, getattr(user, "username", None))
    return {k: v for k, v in run.items() if k != "journal"}


# ---------------------------------------------------------------------------
# Rückgängig
# ---------------------------------------------------------------------------
def runs() -> list[dict[str, Any]]:
    state = ops.get_state(STATE_KEY) or {}
    return [{k: v for k, v in r.items() if k != "journal"} for r in state.get("runs") or []]


def undo(user: Any, ip: str | None = None) -> dict[str, Any]:
    from .audit import audit
    from .feature_models.channels import Channel
    from .feature_models.gradebook import GradeBook
    from .store import get_store

    state = ops.get_state(STATE_KEY) or {}
    lst = list(state.get("runs") or [])
    run = next((r for r in lst if not r.get("undone_at")), None)
    if run is None:
        raise HTTPException(404, "Kein Schuljahreswechsel zum Rückgängigmachen vorhanden")
    store = get_store()
    if store.version != run["after_version"]:
        raise HTTPException(409, "Seit dem Wechsel wurde der Plan weiter geändert – ein Rückgängigmachen würde diese "
                                 "Änderungen verwerfen. Bitte im Verlauf gezielt zurückgehen.")
    j = run.get("journal") or {}
    store.restore(user, run["before_version"])
    with session_scope() as db:
        if j.get("users"):
            for u in db.scalars(select(User).where(User.id.in_(j["users"]))).all():
                u.active = True
        if j.get("channels"):
            for ch in db.scalars(select(Channel).where(Channel.id.in_(j["channels"]))).all():
                ch.archived = False
        if j.get("books"):
            for b in db.scalars(select(GradeBook).where(GradeBook.id.in_(j["books"]))).all():
                b.locked_at, b.locked_by, b.locked_by_name = None, None, ""
        audit(db, user, "yearchange.undo", run["new_year"], {"run": run["id"]}, ip=ip)
    run["undone_at"] = iso(utcnow())
    ops.set_state(STATE_KEY, {"runs": lst}, getattr(user, "username", None))
    return {k: v for k, v in run.items() if k != "journal"}
