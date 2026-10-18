"""Löschkonzept und Auskunft (DSGVO Art. 5 Abs. 1 lit. e, Art. 15, 17, 20) – zentrale Registrierung.

Jedes Modul, das personenbezogene Daten speichert, meldet sich hier **einmal** an::

    from schulmanager.server import retention

    def purge(db, ctx):                      # ctx.student_ids, ctx.user_ids, ctx.dry_run
        return retention.purge_rows(db, ctx, MyModel, MyModel.student_id.in_(ctx.student_ids))

    def export(db, subject):                 # subject.user (AuthUser), subject.children(db, area)
        return {"my_section": [...]}

    retention.register("mein_modul", purge, export, label="Meine Daten", category="leistung",
                       legal="Art. 6 Abs. 1 lit. e DSGVO i. V. m. Landesschulgesetz", default_days=180,
                       ids_fn=lambda db: set(db.scalars(select(MyModel.student_id))))

* ``purge_fn(db, ctx) -> int`` löscht (oder anonymisiert) alle Daten der Person(en) in ``ctx`` und gibt die Anzahl
  zurück. Bei ``ctx.dry_run`` darf **nichts** verändert werden – nur zählen (Vorschau „Was würde gelöscht“).
* ``export_fn(db, subject) -> dict`` liefert die Abschnitte der Auskunft (``/me/export`` und Auskunft der Schulleitung).
* ``default_days`` – Frist **nach dem Austritt** (Tage); die Schule ändert sie in den Einstellungen. Mindestens gilt die
  Warteliste-Frist ``grace_days``.
* ``age_default`` + ``expire_fn(db, today, days, dry_run) -> int`` – optional: laufende Löschung nach Alter, unabhängig
  vom Austritt (z. B. Krankmeldungen: Ende des Schuljahres + Frist).
* ``ids_fn(db) -> set[str]`` – optional: die Personen-IDs, die das Modul kennt (erkennt Ausgetretene).
* ``last=True`` – läuft erst, wenn alle anderen Datenarten der Person bereinigt sind (Konten).

Ablauf (:func:`run`, stündlich in ``maintenance.run_maintenance``): :func:`sync_leavers` trägt Personen, die nicht mehr im
Planungsdokument stehen, in die Warteliste „ausgetreten“ ein (Konto wird gesperrt). Nach Ablauf der Frist je Datenart
löscht :func:`run` die Daten; das Löschprotokoll (``retention_log``) hält Datenart, Anzahl und Zeitpunkt fest – nie Inhalte.
:func:`erase_student` ist das sofortige Löschen nach Art. 17. Dokumentation: ``docs/DATENSCHUTZ-LOESCHKONZEPT.md``.
"""
from __future__ import annotations

import html
import json
import logging
import os
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any, Callable, Iterable, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from . import crypto
from .audit import audit
from .db import iso, session_scope, utcnow
from .db_models import AuditLog, SchoolVersion, User
from .feature_models.retention import RetentionLeaver, RetentionLog, RetentionSetting

log = logging.getLogger("schulmanager.retention")

CATEGORIES: dict[str, str] = {
    "gesundheit": "Gesundheits- und Förderdaten (Art. 9 DSGVO)",
    "leistung": "Leistung und Lernstand",
    "unterricht": "Unterricht und Kursräume",
    "kommunikation": "Kommunikation",
    "konto": "Konten und Verknüpfungen",
    "system": "Protokolle und Verlauf",
}
DEFAULT_GRACE_DAYS = 30
DEFAULT_LOG_DAYS = 1095
DEFAULT_AUDIT_DAYS = 365
MAX_DAYS = 3650


# ------------------------------------------------------------------------------------------------ Registrierung
@dataclass
class PurgeContext:
    """Wen es betrifft: ``student_ids`` (Planungsdokument), ``user_ids`` (Schüler-Konten bzw. das Konto selbst)."""
    student_ids: list[str] = field(default_factory=list)
    user_ids: list[int] = field(default_factory=list)
    names: list[str] = field(default_factory=list)       # Anzeigenamen (nur für das Bereinigen des Planverlaufs)
    dry_run: bool = False
    actor: str = "system"


@dataclass(frozen=True)
class Kind:
    key: str
    label: str
    category: str
    legal: str
    default_days: int
    purge_fn: Optional[Callable[[Session, PurgeContext], int]]
    export_fn: Optional[Callable[[Session, "Subject"], dict]]
    age_default: Optional[int] = None
    expire_fn: Optional[Callable[[Session, date, int, bool], int]] = None
    ids_fn: Optional[Callable[[Session], set]] = None
    order: int = 100
    last: bool = False
    how: str = "gelöscht"          # Löschweg in Worten (Doku/Oberfläche)
    description: str = ""


_KINDS: dict[str, Kind] = {}


def register(kind: str, purge_fn: Optional[Callable[[Session, PurgeContext], int]] = None,
             export_fn: Optional[Callable[[Session, "Subject"], dict]] = None, *, label: str = "",
             category: str = "unterricht", legal: str = "", default_days: int = DEFAULT_GRACE_DAYS,
             age_default: Optional[int] = None, expire_fn: Optional[Callable[[Session, date, int, bool], int]] = None,
             ids_fn: Optional[Callable[[Session], set]] = None, order: int = 100, last: bool = False,
             how: str = "gelöscht", description: str = "") -> Kind:
    """Meldet eine Datenart am Löschkonzept und an der Auskunft an (idempotent: erneutes Anmelden ersetzt)."""
    if category not in CATEGORIES:
        raise ValueError(f"Unbekannte Kategorie {category!r}")
    if not kind or "." in kind or ":" in kind:
        raise ValueError("Ungültiger Schlüssel")
    entry = Kind(kind, label or kind, category, legal, int(default_days), purge_fn, export_fn, age_default, expire_fn,
                 ids_fn, order, last, how, description)
    _KINDS[kind] = entry
    return entry


def kinds() -> list[Kind]:
    """Alle angemeldeten Datenarten in Ausführungsreihenfolge."""
    _ensure_builtin()
    return sorted(_KINDS.values(), key=lambda k: (k.last, k.order, k.key))


def get_kind(key: str) -> Optional[Kind]:
    _ensure_builtin()
    return _KINDS.get(key)


_loaded = False


def _ensure_builtin() -> None:
    """Die Datenarten der mitgelieferten Module (``retention_kinds``) beim ersten Zugriff anmelden."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    from . import retention_kinds  # noqa: F401  (Import registriert)


# ------------------------------------------------------------------------------------------------ Hilfen für purge_fn
def purge_rows(db: Session, ctx: PurgeContext, model: Any, *conds: Any) -> int:
    """Löscht Zeilen von ``model`` mit den Bedingungen (bei ``ctx.dry_run`` nur zählen). Massenlöschung ohne
    ORM-Ereignisse (auch für schreibgeschützte Protokolltabellen)."""
    if ctx.dry_run:
        return int(db.scalar(select(func.count()).select_from(model).where(*conds)) or 0)
    return int(db.execute(delete(model).where(*conds)).rowcount or 0)


def count_rows(db: Session, model: Any, *conds: Any) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(*conds)) or 0)


# ------------------------------------------------------------------------------------------------ Einstellungen
def _defaults() -> dict[str, str]:
    audit_days = DEFAULT_AUDIT_DAYS
    raw = os.environ.get("SM_AUDIT_RETENTION_DAYS")
    if raw not in (None, ""):
        try:
            audit_days = max(0, int(raw))
        except ValueError:
            pass
    return {"grace_days": str(DEFAULT_GRACE_DAYS), "auto_purge": "1", "audit_days": str(audit_days),
            "log_days": str(DEFAULT_LOG_DAYS)}


def _load_settings(db: Session) -> dict[str, str]:
    return {r.key: r.value for r in db.scalars(select(RetentionSetting))}


def setting_int(db: Session, key: str, default: int, *, stored: Optional[dict[str, str]] = None) -> int:
    values = stored if stored is not None else _load_settings(db)
    try:
        return max(0, min(MAX_DAYS, int(values[key]))) if key in values else default
    except (TypeError, ValueError):
        return default


def grace_days(db: Session, stored: Optional[dict[str, str]] = None) -> int:
    return setting_int(db, "grace_days", int(_defaults()["grace_days"]), stored=stored)


def days_after_exit(db: Session, kind: Kind, stored: Optional[dict[str, str]] = None) -> int:
    """Wirksame Frist nach Austritt: mindestens die Wartelisten-Frist."""
    values = stored if stored is not None else _load_settings(db)
    own = setting_int(db, f"{kind.key}.days", kind.default_days, stored=values)
    return max(own, grace_days(db, values))


def age_days(kind_key: str, default: int) -> int:
    """Alters-Frist einer Datenart (``0`` = aus). Für Module, die ihre Wartung selbst ausführen (Dokumente, Formulare):
    die Einstellung der Schule hat Vorrang vor der Umgebungsvariable (``default``)."""
    try:
        with session_scope() as db:
            return setting_int(db, f"{kind_key}.age_days", default)
    except Exception:  # noqa: BLE001 - Wartung darf nie an der Einstellung scheitern
        return default


def get_settings(db: Session) -> dict[str, Any]:
    """Wirksame Einstellungen samt Standards (für die Oberfläche)."""
    stored = _load_settings(db)
    d = _defaults()
    out: dict[str, Any] = {
        "grace_days": setting_int(db, "grace_days", int(d["grace_days"]), stored=stored),
        "auto_purge": stored.get("auto_purge", d["auto_purge"]) == "1",
        "audit_days": setting_int(db, "audit_days", int(d["audit_days"]), stored=stored),
        "log_days": setting_int(db, "log_days", int(d["log_days"]), stored=stored),
        "defaults": {"grace_days": int(d["grace_days"]), "audit_days": int(d["audit_days"]),
                     "log_days": int(d["log_days"])},
        "kinds": [],
    }
    for k in kinds():
        age_def = k.age_default
        if age_def is not None and k.key in ("documents", "forms"):
            from .config import config
            age_def = config.student_docs_retention_days
        out["kinds"].append({
            "key": k.key, "label": k.label, "category": k.category, "category_label": CATEGORIES[k.category],
            "legal": k.legal, "how": k.how, "description": k.description, "last": k.last,
            "days": setting_int(db, f"{k.key}.days", k.default_days, stored=stored), "default_days": k.default_days,
            "effective_days": days_after_exit(db, k, stored),
            "age_days": None if age_def is None else setting_int(db, f"{k.key}.age_days", age_def, stored=stored),
            "age_default": age_def, "has_age": age_def is not None,
        })
    return out


def save_settings(db: Session, changes: dict[str, Any], actor: str) -> list[str]:
    """Speichert Einstellungen (ohne Commit); gibt die geänderten Schlüssel zurück. Werte werden begrenzt."""
    known = {k.key for k in kinds()}
    changed: list[str] = []

    def put(key: str, value: str) -> None:
        row = db.get(RetentionSetting, key)
        if row is None:
            db.add(RetentionSetting(key=key, value=value, updated_by=actor[:80]))
            changed.append(key)
        elif row.value != value:
            row.value, row.updated_at, row.updated_by = value, utcnow(), actor[:80]
            changed.append(key)

    for key in ("grace_days", "audit_days", "log_days"):
        if changes.get(key) is not None:
            put(key, str(max(0, min(MAX_DAYS, int(changes[key])))))
    if changes.get("auto_purge") is not None:
        put("auto_purge", "1" if changes["auto_purge"] else "0")
    for key, vals in (changes.get("kinds") or {}).items():
        if key not in known:
            continue
        for field_name, suffix in (("days", "days"), ("age_days", "age_days")):
            if (vals or {}).get(field_name) is not None:
                put(f"{key}.{suffix}", str(max(0, min(MAX_DAYS, int(vals[field_name])))))
    return changed


# ------------------------------------------------------------------------------------------------ Warteliste
def _students_in_doc() -> Optional[dict[str, Any]]:
    from .store import get_store
    school = get_store().school
    return school.index("students")


def _known_ids(db: Session) -> set[str]:
    from .db_models import ParentLink
    ids: set[str] = set(db.scalars(select(User.student_id).where(User.student_id.is_not(None),
                                                                 User.role == "schueler")))
    ids |= set(db.scalars(select(ParentLink.student_id)))
    for k in kinds():
        if k.ids_fn is None:
            continue
        try:
            ids |= {str(i) for i in k.ids_fn(db) if i}
        except Exception:  # noqa: BLE001
            log.exception("ids_fn der Datenart %s fehlgeschlagen", k.key)
    return ids


def _history_names(wanted: set[str]) -> dict[str, tuple[str, str]]:
    """Name und Klasse der gesuchten Personen aus den neuesten Planversionen, die sie noch enthalten."""
    found: dict[str, tuple[str, str]] = {}
    if not wanted:
        return found
    from .store import decode_school
    with session_scope() as db:
        for row in db.scalars(select(SchoolVersion).order_by(SchoolVersion.id.desc()).limit(400)):
            try:
                school = decode_school(row.data)
            except Exception:  # noqa: BLE001
                continue
            for s in school.students:
                if s.id in wanted and s.id not in found:
                    found[s.id] = (s.name, s.class_id)
            if len(found) == len(wanted):
                break
    return found


def _lock_accounts(db: Session, student_id: str) -> int:
    from .accounts import revoke_sessions
    n = 0
    for u in db.scalars(select(User).where(User.student_id == student_id, User.role == "schueler")):
        if u.active:
            u.active = False
            n += 1
        revoke_sessions(db, u.id)
    return n


def _unlock_accounts(db: Session, student_id: str) -> int:
    n = 0
    for u in db.scalars(select(User).where(User.student_id == student_id, User.role == "schueler")):
        if not u.active:
            u.active = True
            n += 1
    return n


def sync_leavers(db: Session, now: Optional[datetime] = None) -> dict[str, int]:
    """Gleicht die Warteliste mit dem Planungsdokument ab (ohne Commit): wer fehlt, kommt hinein (Konto gesperrt);
    wer wieder im Dokument steht, kommt heraus. Ein leeres Schülerverzeichnis wird nie als „alle ausgetreten“
    gewertet (z. B. frisch eingerichtete Instanz)."""
    now = now or utcnow()
    doc = _students_in_doc()
    out = {"added": 0, "returned": 0}
    if not doc:
        return out
    rows = {r.student_id: r for r in db.scalars(select(RetentionLeaver))}
    for sid, row in list(rows.items()):
        if sid in doc and row.status == "wartend":
            _unlock_accounts(db, sid)
            db.delete(row)
            out["returned"] += 1
            log.info("Person %s ist wieder im Planungsdokument – aus der Warteliste entfernt", sid)
    missing = {s for s in _known_ids(db) if s not in doc}
    fresh = {s for s in missing if s not in rows or rows[s].status == "erledigt"}
    if not fresh:
        return out
    names = _history_names(fresh)
    for sid in sorted(fresh):
        row = rows.get(sid)
        if row is None:
            row = RetentionLeaver(student_id=sid, status="wartend", source="abgleich", left_at=now, purged=[])
            db.add(row)
            db.flush()
        else:                                   # ID erneut aufgetaucht, nachdem sie bereits bereinigt war
            row.status, row.left_at, row.purged, row.done_at = "wartend", now, [], None
        name, class_id = names.get(sid, ("", ""))
        if name:
            row.name_enc = crypto.encrypt_text(name, row.name_aad)
        row.class_id = class_id
        _lock_accounts(db, sid)
        audit(db, None, "privacy.leaver", f"student:{sid}", {"frist_tage": grace_days(db)})
        out["added"] += 1
    return out


def leaver_name(row: RetentionLeaver) -> str:
    if not row.name_enc:
        return ""
    try:
        return crypto.decrypt_text(row.name_enc, row.name_aad)
    except crypto.CryptoError:
        return ""


def cancel_leaver(db: Session, student_id: str) -> bool:
    """Austritt zurücknehmen (nur wenn die Person wieder im Planungsdokument steht). Ohne Commit."""
    row = db.scalar(select(RetentionLeaver).where(RetentionLeaver.student_id == student_id,
                                                  RetentionLeaver.status == "wartend"))
    if row is None:
        return False
    doc = _students_in_doc() or {}
    if student_id not in doc:
        raise ValueError("Die Person steht nicht im Planungsdokument – zuerst wieder unter Stammdaten anlegen.")
    _unlock_accounts(db, student_id)
    db.delete(row)
    return True


# ------------------------------------------------------------------------------------------------ Löschen
def _student_users(db: Session, student_id: str) -> list[int]:
    return list(db.scalars(select(User.id).where(User.student_id == student_id, User.role == "schueler")))


def _log(db: Session, kind: str, count: int, *, mode: str, subject: str, actor: str, action: str = "geloescht",
         note: str = "") -> None:
    db.add(RetentionLog(kind=kind, count=int(count), mode=mode, subject=subject, actor=actor[:80], action=action,
                        note=note[:200]))


def _due_at(row: RetentionLeaver, days: int) -> datetime:
    return row.left_at + timedelta(days=days)


def process_leaver(db: Session, row: RetentionLeaver, now: datetime, *, dry_run: bool = False, force: bool = False,
                   mode: str = "frist", actor: str = "system") -> list[dict]:
    """Bereinigt die fälligen Datenarten einer Person (``force``: alle sofort). Ein Fehler einer Datenart stoppt die
    übrigen nicht, verhindert aber den Abschluss. Gibt je Datenart ``{kind,label,count,due_at,due,done}`` zurück."""
    stored = _load_settings(db)
    purged = set(row.purged or [])
    ctx = PurgeContext(student_ids=[row.student_id], user_ids=_student_users(db, row.student_id),
                       names=[n for n in [leaver_name(row)] if n], dry_run=dry_run, actor=actor)
    results: list[dict] = []
    all_kinds = [k for k in kinds() if k.purge_fn is not None]
    failed = False
    for k in all_kinds:
        due = _due_at(row, days_after_exit(db, k, stored))
        item = {"kind": k.key, "label": k.label, "count": 0, "due_at": iso(due), "due": force or now >= due,
                "done": k.key in purged}
        if item["done"]:
            results.append(item)
            continue
        if k.last and not all(o.key in purged or o.key == k.key for o in all_kinds if not o.last) and not dry_run:
            item["due"] = False
            results.append(item)
            continue
        if not item["due"] and not dry_run:
            results.append(item)
            continue
        try:
            with db.begin_nested():
                item["count"] = int(k.purge_fn(db, ctx) or 0)     # type: ignore[misc]
        except Exception:  # noqa: BLE001
            log.exception("Löschen der Datenart %s für %s fehlgeschlagen", k.key, row.student_id)
            item["error"] = True
            failed = True
            results.append(item)
            continue
        if not dry_run and item["due"]:
            purged.add(k.key)
            item["done"] = True
            if item["count"]:
                _log(db, k.key, item["count"], mode=mode, subject=f"student:{row.student_id}", actor=actor,
                     action="anonymisiert" if k.how == "anonymisiert" else "geloescht")
        results.append(item)
    if not dry_run:
        row.purged = sorted(purged)
        if not failed and all(k.key in purged for k in all_kinds):
            _finish_leaver(db, row, mode=mode, actor=actor)
    return results


def _finish_leaver(db: Session, row: RetentionLeaver, *, mode: str, actor: str) -> None:
    row.status, row.done_at, row.name_enc = "erledigt", utcnow(), ""
    audit(db, None, "privacy.purged", f"student:{row.student_id}", {"modus": mode, "durch": actor})
    _log(db, "person", 1, mode=mode, subject=f"student:{row.student_id}", actor=actor, action="abgeschlossen")


def run(now: Optional[datetime] = None, *, dry_run: bool = False) -> dict[str, int]:
    """Wartungslauf des Löschkonzepts: Warteliste abgleichen, Fälliges löschen, Alters-Fristen, Protokoll-Fristen.
    Rückgabe: Zähler für das Wartungsprotokoll."""
    now = now or utcnow()
    result = {"leavers_added": 0, "leavers_done": 0, "rows_purged": 0, "rows_expired": 0, "audit_purged": 0}
    with session_scope() as db:
        s = sync_leavers(db, now)
        result["leavers_added"] = s["added"]
        auto = _load_settings(db).get("auto_purge", "1") == "1"
        if auto:
            for row in db.scalars(select(RetentionLeaver).where(RetentionLeaver.status == "wartend")
                                  .order_by(RetentionLeaver.id)).all():
                res = process_leaver(db, row, now, dry_run=dry_run, mode="frist")
                result["rows_purged"] += sum(r["count"] for r in res if r["done"] and r["count"])
                if row.status == "erledigt":
                    result["leavers_done"] += 1
    with session_scope() as db:
        exp = run_expire(db, now, dry_run=dry_run)
        result["rows_expired"] = sum(v for k, v in exp.items() if k != "audit")
        result["audit_purged"] = exp.get("audit", 0)
    return result


def run_expire(db: Session, now: datetime, *, dry_run: bool = False) -> dict[str, int]:
    """Alters-Fristen (unabhängig vom Austritt): Datenarten mit ``expire_fn``, Audit-Log, Löschprotokoll."""
    stored = _load_settings(db)
    out: dict[str, int] = {}
    for k in kinds():
        if k.expire_fn is None or k.age_default is None:
            continue
        days = setting_int(db, f"{k.key}.age_days", k.age_default, stored=stored)
        if days <= 0:
            continue
        try:
            with db.begin_nested():
                n = int(k.expire_fn(db, now.date(), days, dry_run) or 0)
        except Exception:  # noqa: BLE001
            log.exception("Alters-Frist der Datenart %s fehlgeschlagen", k.key)
            continue
        out[k.key] = n
        if n and not dry_run:
            _log(db, k.key, n, mode="frist", subject="", actor="system", note=f"älter als {days} Tage")
    audit_d = setting_int(db, "audit_days", int(_defaults()["audit_days"]), stored=stored)
    if audit_d > 0:
        cutoff = now - timedelta(days=audit_d)
        if dry_run:
            n = count_rows(db, AuditLog, AuditLog.created_at < cutoff)
        else:
            n = int(db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff)).rowcount or 0)
            if n:
                _log(db, "audit", n, mode="frist", subject="", actor="system", note=f"älter als {audit_d} Tage")
        out["audit"] = n
    log_d = setting_int(db, "log_days", int(_defaults()["log_days"]), stored=stored)
    if log_d > 0 and not dry_run:
        cutoff = now - timedelta(days=log_d)
        db.execute(delete(RetentionLog).where(RetentionLog.at < cutoff))
        db.execute(delete(RetentionLeaver).where(RetentionLeaver.status == "erledigt",
                                                 RetentionLeaver.done_at < cutoff))
    return out


def preview(db: Session, now: Optional[datetime] = None, student_id: Optional[str] = None) -> dict[str, Any]:
    """„Was würde gelöscht“: je ausgetretener Person und Datenart die Anzahl (nichts wird verändert)."""
    now = now or utcnow()
    people = []
    q = select(RetentionLeaver).where(RetentionLeaver.status == "wartend").order_by(RetentionLeaver.left_at)
    if student_id:
        q = q.where(RetentionLeaver.student_id == student_id)
    for row in db.scalars(q).all():
        with db.begin_nested():
            res = process_leaver(db, row, now, dry_run=True)
        items = [r for r in res if not r["done"]]
        people.append({"student_id": row.student_id, "name": leaver_name(row), "class_id": row.class_id,
                       "left_at": iso(row.left_at), "items": items,
                       "total": sum(r["count"] for r in items), "due_total": sum(r["count"] for r in items if r["due"])})
    with db.begin_nested():
        exp = run_expire(db, now, dry_run=True)
    labels = {k.key: k.label for k in kinds()}
    labels["audit"] = "Audit-Protokoll"
    expiry = [{"kind": k, "label": labels.get(k, k), "count": v} for k, v in exp.items() if v]
    return {"people": people, "expiry": expiry, "generated_at": iso(now)}


def erase_student(db: Session, student_id: str, actor: Any, *, reason: str = "", ip: Optional[str] = None) -> dict:
    """Sofortiges Löschen einer Person nach Art. 17 DSGVO (ohne Commit): entfernt sie aus dem Planungsdokument,
    löscht alle registrierten Datenarten und den Planverlauf. Berechtigung und Bestätigung prüft der Aufrufer."""
    from .store import get_store
    store = get_store()
    doc = store.school.index("students")
    name, class_id = (doc[student_id].name, doc[student_id].class_id) if student_id in doc else ("", "")
    if not name:
        name, class_id = _history_names({student_id}).get(student_id, ("", ""))
    row = db.scalar(select(RetentionLeaver).where(RetentionLeaver.student_id == student_id))
    if row is None:
        row = RetentionLeaver(student_id=student_id, status="wartend", source="planung", left_at=utcnow(), purged=[])
        db.add(row)
        db.flush()
    else:
        row.status, row.purged, row.done_at = "wartend", [], None
    if name:
        row.name_enc = crypto.encrypt_text(name, row.name_aad)
    row.class_id = class_id
    if student_id in doc:
        db.commit()                 # Schreibsperre freigeben: das Planungsdokument schreibt in eigener Sitzung
        _remove_from_plan(actor, student_id)
        row = db.scalar(select(RetentionLeaver).where(RetentionLeaver.student_id == student_id))
        assert row is not None
    actor_name = getattr(actor, "username", None) or "system"
    results = process_leaver(db, row, utcnow(), force=True, mode="sofort", actor=actor_name)
    audit(db, actor, "privacy.erase", f"student:{student_id}",
          {"grund": (reason or "")[:200], "datenarten": sum(1 for r in results if r["done"]), "ip": ip})
    return {"student_id": student_id, "status": row.status, "items": results,
            "total": sum(r["count"] for r in results)}


def _remove_from_plan(actor: Any, student_id: str) -> None:
    from .routes.features_data import cascade_delete
    from .store import get_store

    def fn(school):
        cascade_delete(school, "students", student_id)
        school.students = [s for s in school.students if s.id != student_id]

    get_store().mutate(actor, f"Person {student_id} auf Antrag gelöscht (Art. 17)", fn, scope=["students"])


def erase_user(db: Session, user_id: int, actor: Any, *, reason: str = "") -> dict:
    """Sofortiges Löschen eines Kontos ohne Schüler-Bezug (z. B. Eltern, Personal): löscht die kontogebundenen Daten
    der registrierten Datenarten und das Konto. Ohne Commit."""
    row = db.get(User, user_id)
    if row is None:
        raise LookupError("Konto nicht gefunden")
    ctx = PurgeContext(student_ids=[], user_ids=[user_id], names=[row.display_name or ""], actor=getattr(actor, "username", "system"))
    items = []
    for k in kinds():
        if k.purge_fn is None or k.key in _STUDENT_ONLY:
            continue
        with db.begin_nested():
            n = int(k.purge_fn(db, ctx) or 0)
        items.append({"kind": k.key, "label": k.label, "count": n})
        if n:
            _log(db, k.key, n, mode="sofort", subject=f"user:{user_id}", actor=ctx.actor)
    audit(db, actor, "privacy.erase", f"user:{user_id}", {"grund": (reason or "")[:200]})
    return {"user_id": user_id, "items": items, "total": sum(i["count"] for i in items)}


# Datenarten, die nur über die Schüler-ID wirken (beim Löschen eines reinen Kontos übersprungen)
_STUDENT_ONLY = {"history"}


# ------------------------------------------------------------------------------------------------ Auskunft
@dataclass
class Subject:
    """Die Person, für die Auskunft erteilt wird. ``user`` ist ihre Sicht (Rechte wie in der Oberfläche)."""
    user: Any                    # AuthUser
    row: User

    @property
    def uid(self) -> int:
        return int(self.row.id)

    def children(self, db: Session, area: Optional[str] = None) -> list[str]:
        """Personen-IDs, deren Daten in die Auskunft gehören: Schüler/in selbst; Eltern die Kinder, soweit
        ``parent_access`` den Bereich ``area`` freigibt (``None`` = nur mit Volljährigkeits-Prüfung aller Bereiche)."""
        role = self.row.role
        if role == "schueler":
            return [self.row.student_id] if self.row.student_id else []
        if role == "eltern":
            ids = list(getattr(self.user, "student_ids", None) or [])
            if area is None:
                return ids
            from . import parent_access
            return parent_access.visible_children(db, ids, area)
        return []

    def child_user_ids(self, db: Session, area: Optional[str] = None) -> list[int]:
        """Eigenes Konto (Schüler) bzw. die Schüler-Konten der Kinder (Eltern)."""
        if self.row.role == "schueler":
            return [self.uid]
        sids = self.children(db, area)
        if not sids:
            return []
        return list(db.scalars(select(User.id).where(User.student_id.in_(sids), User.role == "schueler")))

    def is_minor_child_ids(self, db: Session) -> list[str]:
        """Für Eltern: nur minderjährige Kinder (für Daten ohne eigenen Freigabebereich, z. B. Förderdaten)."""
        if self.row.role == "schueler":
            return self.children(db)
        from . import parent_access
        return [s for s in self.children(db) if not parent_access.is_adult(db, s)]


def collect_export(db: Session, subject: Subject) -> dict[str, Any]:
    """Führt alle ``export_fn`` aus und fügt die Abschnitte zusammen. Ein Fehler einer Datenart bricht die Auskunft
    nicht ab, wird aber unter ``hinweise`` vermerkt (Vollständigkeit prüfbar)."""
    data: dict[str, Any] = {}
    notes: list[str] = []
    for k in kinds():
        if k.export_fn is None:
            continue
        try:
            part = k.export_fn(db, subject) or {}
        except Exception:  # noqa: BLE001
            log.exception("Auskunft: Datenart %s fehlgeschlagen", k.key)
            notes.append(f"{k.label}: konnte nicht vollständig ausgelesen werden")
            continue
        for key, value in part.items():
            data[key] = value
    if notes:
        data["hinweise"] = notes
    return data


SECTION_LABELS: dict[str, str] = {
    "exported_at": "Erstellt am", "account": "Konto", "permissions": "Rechte", "two_factor_enabled": "Zwei-Faktor aktiv",
    "ical_link_active": "Kalender-Link aktiv", "sessions": "Anmeldesitzungen", "api_tokens": "Zugriffs-Tokens",
    "login_attempts": "Anmeldeversuche", "audit_log": "Protokoll der Aktionen", "students": "Stammdaten (Schüler/in)",
    "teacher": "Stammdaten (Lehrkraft)", "contact": "Kontaktdaten", "identities": "Verbundene Anbieter-Konten",
    "announcements_authored": "Verfasste Mitteilungen", "teacher_change_requests": "Profil-Anträge",
    "hinweise": "Hinweise", "hinweis_chats": "Hinweis zu Chats",
}


def label_for(section: str) -> str:
    if section in SECTION_LABELS:
        return SECTION_LABELS[section]
    return section.replace("_", " ").capitalize()


def _render(value: Any, level: int = 0) -> str:
    if value is None or value == "":
        return '<span class="n">–</span>'
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, (int, float)):
        return html.escape(str(value))
    if isinstance(value, str):
        return html.escape(value).replace("\n", "<br>")
    if isinstance(value, dict):
        if not value:
            return '<span class="n">–</span>'
        rows = "".join(f"<tr><th>{html.escape(label_for(str(k)))}</th><td>{_render(v, level + 1)}</td></tr>"
                       for k, v in value.items())
        return f"<table>{rows}</table>"
    if isinstance(value, (list, tuple)):
        if not value:
            return '<span class="n">keine Einträge</span>'
        if all(isinstance(v, dict) for v in value) and all(
                not isinstance(x, (dict, list)) for v in value for x in v.values()):
            cols = list(dict.fromkeys(c for v in value for c in v))
            head = "".join(f"<th>{html.escape(label_for(str(c)))}</th>" for c in cols)
            body = "".join("<tr>" + "".join(f"<td>{_render(v.get(c), level + 1)}</td>" for c in cols) + "</tr>"
                           for v in value)
            return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        return "<ul>" + "".join(f"<li>{_render(v, level + 1)}</li>" for v in value) + "</ul>"
    return html.escape(str(value))


def overview_html(data: dict[str, Any], title: str) -> str:
    """Lesbare Übersicht der Auskunft (eigenständige HTML-Seite, ohne Skripte)."""
    parts = []
    for key, value in data.items():
        parts.append(f"<section><h2>{html.escape(label_for(key))}</h2>{_render(value)}</section>")
    css = ("body{font:15px/1.5 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#111}"
           "h1{font-size:1.5rem}h2{font-size:1.15rem;margin-top:2rem;border-bottom:1px solid #ccc}"
           "table{border-collapse:collapse;margin:.4rem 0;width:100%}th,td{border:1px solid #ddd;padding:.25rem .5rem;"
           "text-align:left;vertical-align:top}th{background:#f3f3f3}.n{color:#777}")
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head>'
            f"<body><h1>{html.escape(title)}</h1>"
            "<p>Auskunft nach Art. 15 und 20 DSGVO. Die Datei <code>daten.json</code> enthält dieselben Angaben "
            "maschinenlesbar.</p>" + "".join(parts) + "</body></html>")


def export_zip(data: dict[str, Any], title: str) -> bytes:
    """ZIP mit ``daten.json`` (maschinenlesbar) und ``uebersicht.html`` (lesbar)."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("daten.json", json.dumps(data, ensure_ascii=False, indent=2, default=str))
        zf.writestr("uebersicht.html", overview_html(data, title))
    return buf.getvalue()


# ------------------------------------------------------------------------------------------------ Hilfen für Module
def school_year_end_before(today: date, days: int) -> date:
    """Letzter 31. Juli, der vor ``today - days`` liegt: Alles bis dahin ist „Ende des Schuljahres + Frist“ abgelaufen."""
    t = today - timedelta(days=days)
    cand = date(t.year, 7, 31)
    return cand if cand < t else date(t.year - 1, 7, 31)


def plain_rows(rows: Iterable[Any]) -> list[dict]:
    """ORM-Zeilen → Dicts mit Klartext-Spalten (Hilfe für einfache Exporte)."""
    out = []
    for obj in rows:
        item = {}
        for col in obj.__table__.columns:
            value = getattr(obj, col.key)
            if col.key.endswith("_enc"):
                continue
            item[col.key] = iso(value) if isinstance(value, datetime) else value
        out.append(item)
    return out
