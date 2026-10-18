"""Gemeinsame Hilfsfunktionen der Feature-Endpunkte.

Dieses Modul exportiert bewusst **keinen** ``router`` – es enthält

* den Zugriff auf Store/Event-Bus (``snapshot``, ``mutate``),
* LRU-Caches für Vertretungspläne (``(store.version, datum)``) und abgeleitete Daten,
* Rechte-/Sichtbarkeitsregeln (Rollenmatrix aus ``docs/ARCHITECTURE.md`` §6),
* das Filtern/Bereinigen von Vertretungsplänen je Rolle.

Lehrer-Scope (§9.3): ``plans.read_all`` ist für Lehrkräfte auf ``own_classes`` beschränkt. Sie sehen nur
Pläne/Einträge ihrer Klassen (unterrichtet oder Klassenleitung), ihren eigenen Plan und Räume – nie fremde
Lehrerpläne oder Schülerdaten fremder Klassen. Hilfen: ``reads_all_plans``, ``is_scoped_teacher``,
``teacher_entry_filter``, ``plan_class_ids``.
"""
from __future__ import annotations

import inspect
import re
import threading
from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import Any, Callable, Iterable, Optional

from fastapi import HTTPException

from schulmanager.models import School

# Rollen, deren Recht ``students.read`` auf eigene Klassen beschränkt ist.
RESTRICTED_STUDENT_ROLES = {"lehrer"}
MAX_RANGE_DAYS = 62


# ----------------------------------------------------------------- Rechte
def has(user, perm: str) -> bool:
    return perm in (getattr(user, "permissions", None) or set())


def need(user, *perms: str) -> None:
    """403, wenn der Benutzer keines der Rechte besitzt."""
    if not any(has(user, p) for p in perms):
        raise HTTPException(403, "Keine Berechtigung")


def own_student_ids(user) -> list[str]:
    """Schüler: eigene ID; Eltern: Kinder."""
    ids = list(getattr(user, "student_ids", None) or [])
    sid = getattr(user, "student_id", None)
    if sid and sid not in ids:
        ids.insert(0, sid)
    return ids


def perm_scope(user, perm: str) -> Optional[str]:
    """Einschränkung eines Rechts (``own_classes``, ``own``, ``own_children``, ``own_courses`` …)
    laut ``permissions.PERMISSION_SCOPES``; ``None`` = uneingeschränkt."""
    fn = getattr(user, "scope", None)
    if callable(fn):
        try:
            return fn(perm)
        except Exception:  # pragma: no cover
            pass
    try:
        from schulmanager.server.permissions import scope_for
        return scope_for(getattr(user, "role", ""), perm)
    except Exception:  # pragma: no cover
        return "own_classes" if getattr(user, "role", "") in RESTRICTED_STUDENT_ROLES else None


def reads_all_plans(user) -> bool:
    """``plans.read_all`` ohne Einschränkung (alle Klassen, Lehrkräfte, Räume, Schulstatistik)."""
    return has(user, "plans.read_all") and perm_scope(user, "plans.read_all") is None


def is_scoped_teacher(user) -> bool:
    """Lehrkraft mit eingeschränktem Planzugriff (``plans.read_all`` → ``own_classes``; Abteilungsleitung:
    ``own_branch`` = geleitete Klassen + Klassen des eigenen Zweigs)."""
    return has(user, "plans.read_all") and perm_scope(user, "plans.read_all") in ("own_classes", "own_branch")


# ----------------------------------------------------------------- Store
def get_store():
    from schulmanager.server.store import get_store as _get
    return _get()


class Snap(tuple):
    """``(version, school)`` plus Cache-Schlüssel ``key`` (Version + Inhalts-Digest).

    Der Digest unterscheidet gleiche Versionsnummern verschiedener Datenbanken (Tests,
    Neuinstallation, Wiederherstellung)."""
    key: Any = None


def snapshot() -> Snap:
    """Liefert ``(version, school)`` – Version/Digest zuerst lesen, dann das Dokument
    (ein gleichzeitiges ``mutate`` kann so höchstens einen *neueren* Stand unter altem
    Schlüssel ablegen, nie umgekehrt)."""
    st = get_store()
    ver = st.version
    digest = getattr(st, "digest", None) or getattr(st, "_digest", None) or id(st)
    snap = Snap((ver, st.school))
    snap.key = (ver, digest)
    return snap


def snap_key(snap) -> Any:
    return getattr(snap, "key", None) or snap[0]


_mutate_has_dates: Optional[bool] = None


def mutate(user, message: str, fn: Callable[[School], Any], scope: list[str],
           dates: Optional[Iterable[str]] = None, *, action: Optional[str] = None,
           details: Optional[dict] = None) -> Any:
    """``store.mutate`` mit optionalen ``dates`` (für gezieltes Neuladen der Clients) und eigener Audit-Aktion."""
    global _mutate_has_dates
    st = get_store()
    date_list = sorted(set(dates)) if dates else []
    if _mutate_has_dates is None:
        try:
            _mutate_has_dates = "dates" in inspect.signature(st.mutate).parameters
        except (TypeError, ValueError):
            _mutate_has_dates = False
    extra: dict = {}
    if action:
        extra["action"] = action
        if details:
            extra["details"] = details
    if _mutate_has_dates:
        result = st.mutate(user, message, fn, scope=scope, dates=date_list, **extra)
    else:
        result = st.mutate(user, message, fn, scope=scope, **extra)
        if date_list:
            publish("change", {"version": st.version, "scope": scope, "dates": date_list})
    try:
        from schulmanager.server import notify
        notify.kick()
    except Exception:  # pragma: no cover - Benachrichtigungen dürfen nie stören
        pass
    return result


def publish(event: str, data: dict) -> None:
    try:
        from schulmanager.server.events import bus
        bus.publish(event, data)
    except Exception:  # pragma: no cover
        pass


def publish_change(scope: list[str], dates: Optional[Iterable[str]] = None) -> None:
    """Event für Änderungen außerhalb des Planungsdokuments (DB-Tabellen)."""
    try:
        ver = get_store().version
    except Exception:  # pragma: no cover
        ver = None
    publish("change", {"version": ver, "scope": scope, "dates": sorted(set(dates or []))})


def write_audit(db, user, action: str, target: str, details: Optional[dict] = None) -> None:
    try:
        from schulmanager.server.audit import audit
        audit(db, user, action, target, details or {})
    except Exception:  # pragma: no cover - Audit darf die Aktion nicht verhindern
        pass


# ----------------------------------------------------------------- Datum
def parse_date(value: Optional[str], default: Optional[date] = None, name: str = "date") -> date:
    if value in (None, ""):
        return default or date.today()
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise HTTPException(422, f"Ungültiges Datum für {name}: {value}") from None


def date_range(d1: date, d2: date) -> list[date]:
    return [d1 + timedelta(days=i) for i in range((d2 - d1).days + 1)]


def check_range(d1: date, d2: date, max_days: int = MAX_RANGE_DAYS) -> None:
    if d2 < d1:
        raise HTTPException(422, "Das Enddatum liegt vor dem Startdatum")
    if (d2 - d1).days >= max_days:
        raise HTTPException(422, f"Zeitraum zu lang (maximal {max_days} Tage)")


def iso_dates(d1: date, d2: date, limit: int = 366) -> list[str]:
    days = date_range(d1, d2) if d2 >= d1 else [d1]
    return [d.isoformat() for d in days[:limit]]


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


# ----------------------------------------------------------------- LRU-Cache
class LRUCache:
    """Thread-sicherer LRU-Cache; gleichzeitige Anfragen für denselben Schlüssel
    berechnen den Wert nur einmal (wichtig bei 2500 Schülern um 7:30 Uhr)."""

    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._data: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._inflight: dict[Any, threading.Lock] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key, compute: Callable[[], Any]):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                self.hits += 1
                return self._data[key]
            klock = self._inflight.setdefault(key, threading.Lock())
        with klock:
            with self._lock:
                if key in self._data:
                    self._data.move_to_end(key)
                    self.hits += 1
                    return self._data[key]
            try:
                value = compute()
                with self._lock:
                    self.misses += 1
                    self._data[key] = value
                    while len(self._data) > self.maxsize:
                        self._data.popitem(last=False)
                return value
            finally:
                with self._lock:
                    self._inflight.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


plan_cache = LRUCache(256)       # (version, datum) -> (DayPlan, dict)
derived_cache = LRUCache(8192)   # abgeleitete Daten (effective_day, Schüler-Kurse, ...)


def clear_caches() -> None:
    for c in (plan_cache, derived_cache):
        c.clear()


def day_plan(day: date, snap: Optional[tuple[Any, School]] = None, proposals: bool = False) -> tuple[Any, dict]:
    """Vertretungsplan eines Tages: ``(DayPlan, DayPlan.to_dict())`` – gecacht pro ``(version, datum)``.

    Mit fairer Wochenhistorie (Vertretungen Mo..Vortag, ebenfalls aus dem Cache) – damit identisch
    mit ``substitution.compute_range``. Das Dict ist geteilt und darf **nicht** verändert werden
    (``filter_plan`` kopiert).

    Bestätigungsmodus (``settings.substitution_confirm``): ohne ``proposals`` fehlen die noch nicht freigegebenen
    automatischen Vertretungen (Sicht für alle außer der Vertretungsplanung, Benachrichtigungen, Monitor …); mit
    ``proposals=True`` sind sie enthalten und tragen ``"proposed": true`` (Vertretungsplanung, Fairness-Historie).
    """
    snap = snap or snapshot()
    ver, school = snap

    def compute():
        from schulmanager.substitution import compute_day_plan
        plan = compute_day_plan(school, day, week_history(day, snap))
        return plan, plan.to_dict()

    key = (snap_key(snap), day.isoformat())
    full = plan_cache.get(key, compute)
    if not getattr(school.settings, "substitution_confirm", False):
        return full

    def derive():
        from schulmanager.substitution import mark_proposals, strip_proposals
        if proposals:
            return full[0], mark_proposals(full[1])
        active = strip_proposals(full[0])
        return active, active.to_dict()

    return plan_cache.get(key + ("proposals" if proposals else "active",), derive)


def week_history(day: date, snap) -> dict[str, int]:
    """Vertretungen je Lehrkraft von Montag bis zum Vortag (aus gecachten Tagesplänen)."""
    school = snap[1]
    hist: dict[str, int] = {}
    cur = day - timedelta(days=day.weekday())
    from schulmanager.calendar_utils import open_days
    open_ = set(open_days(school))
    while cur < day:
        if cur.weekday() in open_:   # Wochenlimit Mo–So (Schulöffnungstage)
            plan, _ = day_plan(cur, snap, proposals=True)
            counts = plan.substitution_counts() if hasattr(plan, "substitution_counts") else {}
            for tid, n in counts.items():
                hist[tid] = hist.get(tid, 0) + n
        cur += timedelta(days=1)
    return hist


def range_plans(d1: date, d2: date, snap: Optional[tuple[Any, School]] = None, proposals: bool = False) -> list[dict]:
    """Pläne aller Schulöffnungstage im Bereich (Mo–So, wie ``compute_range``, aber aus dem Cache)."""
    from schulmanager.calendar_utils import open_days
    snap = snap or snapshot()
    days = set(open_days(snap[1]))
    return [day_plan(d, snap, proposals=proposals)[1] for d in date_range(d1, d2) if d.weekday() in days]


def range_plan_objects(d1: date, d2: date, snap=None) -> list[Any]:
    from schulmanager.calendar_utils import open_days
    snap = snap or snapshot()
    days = set(open_days(snap[1]))
    return [day_plan(d, snap)[0] for d in date_range(d1, d2) if d.weekday() in days]


def cached(kind: str, key: tuple, compute: Callable[[], Any], snap=None):
    snap = snap or snapshot()
    return derived_cache.get((kind, snap_key(snap)) + tuple(key), compute)


def index(name: str, snap=None) -> dict[str, Any]:
    """``school.index(name)`` – pro Version gecacht (nicht verändern!)."""
    snap = snap or snapshot()
    return cached("index", (name,), lambda: snap[1].index(name), snap)


def effective_cells(day: date, kind: str, ref: str, snap=None) -> list[dict]:
    """Effektiver Tag (``substitution.effective_day``), gecacht.

    Schülerzellen hängen nur von Klasse und gewählten Kursteilen ab → ein Cache-Eintrag
    je Gruppe statt je Schüler (2500 Schüler ≈ 100 Berechnungen pro Planversion)."""
    snap = snap or snapshot()
    plan, _ = day_plan(day, snap)

    def compute():
        from schulmanager.substitution import effective_day
        return effective_day(snap[1], plan, kind, ref)

    key: tuple = (day.isoformat(), kind, ref)
    if kind == "student":
        st = index("students", snap).get(ref)
        if st is not None:
            parts = student_parts(ref, snap)
            key = (day.isoformat(), "student_group", st.class_id,
                   tuple(sorted((cid, tuple(p)) for cid, p in parts.items())))
    return cached("effective", key, compute, snap)


def student_parts(student_id: str, snap=None) -> dict[str, list[int]]:
    snap = snap or snapshot()

    def compute():
        from schulmanager.timetable import student_parts as _sp
        return _sp(snap[1], student_id)

    return cached("student_parts", (student_id,), compute, snap)


def teacher_class_ids(teacher_id: Optional[str], snap=None) -> frozenset[str]:
    """Klassen, die eine Lehrkraft unterrichtet (inkl. Klassenleitung)."""
    if not teacher_id:
        return frozenset()
    snap = snap or snapshot()

    def compute():
        school = snap[1]
        out = {c.id for c in school.classes if c.class_teacher == teacher_id}
        for course in school.courses:
            if any(p.teacher == teacher_id for p in course.parts):
                out.update(course.classes)
        return frozenset(out)

    return cached("teacher_classes", (teacher_id,), compute, snap)


def teacher_course_ids(teacher_id: Optional[str], snap=None) -> frozenset[str]:
    if not teacher_id:
        return frozenset()
    snap = snap or snapshot()

    def compute():
        return frozenset(c.id for c in snap[1].courses if any(p.teacher == teacher_id for p in c.parts))

    return cached("teacher_courses", (teacher_id,), compute, snap)


def family_student_ids(user, area: str, snap=None) -> list[str]:
    """``own_student_ids`` für einen Elternzugriffs-Bereich (:data:`parent_access.AREAS`): Eltern volljähriger Kinder
    nur, wenn das Kind den Bereich freigegeben hat; Schüler/innen und Minderjährige unverändert."""
    ids = own_student_ids(user)
    if getattr(user, "role", "") != "eltern" or not ids:
        return ids
    from ..db import session_scope
    from ..parent_access import visible_children

    snap = snap or snapshot()
    with session_scope() as db:
        return visible_children(db, ids, area, school=snap[1])


def own_class_ids(user, snap=None) -> frozenset[str]:
    """Klassen, die der Benutzer „als eigene“ sieht (Schüler/Eltern: Klassen der Kinder,
    Lehrkräfte: unterrichtete Klassen)."""
    snap = snap or snapshot()
    ids = own_student_ids(user)
    out: set[str] = set()
    if ids:
        students = index("students", snap)
        out.update(students[s].class_id for s in ids if s in students)
    if getattr(user, "teacher_id", None):
        out.update(teacher_class_ids(user.teacher_id, snap))
    if getattr(user, "branches", None):   # Abteilungsleitung: Klassen des eigenen Zweigs
        from ..permissions import branch_class_ids
        out.update(branch_class_ids(snap[1], user.branches))
    return frozenset(out)


def plan_class_ids(user, snap=None) -> Optional[frozenset[str]]:
    """Klassen, deren Pläne (und Klassenseiten) der Benutzer sehen darf: ``None`` = alle (``plans.read_all`` ohne
    Einschränkung bzw. Planung), Lehrkräfte → nur Klassen, die sie leiten (Wunsch der Schule 2026-10-12),
    Schüler/Eltern → eigene Klasse(n)."""
    if reads_all_plans(user) or has(user, "timetable.edit"):
        return None
    if is_scoped_teacher(user):
        from ..permissions import lead_class_ids
        school = (snap or snapshot())[1]
        lead = set(lead_class_ids(school, getattr(user, "teacher_id", None)))
        if perm_scope(user, "plans.read_all") == "own_branch":
            from ..permissions import branch_class_ids
            lead |= branch_class_ids(school, getattr(user, "branches", None))
        return frozenset(lead)
    return own_class_ids(user, snap)


def plan_course_ids(user, snap=None) -> Optional[frozenset[str]]:
    """Kurse, deren Daten (Stunden, Klausuren) ein Benutzer mit ``plans.read_all`` sehen darf (``None`` = alle):
    Kurse der eigenen Klassen und eigene Kurse."""
    if reads_all_plans(user):
        return None
    snap = snap or snapshot()
    own = own_class_ids(user, snap)
    tid = getattr(user, "teacher_id", None)
    mine = teacher_course_ids(tid, snap) if tid else frozenset()
    return frozenset(c.id for c in snap[1].courses if c.id in mine or set(c.classes) & own)


def teacher_entry_filter(user, snap) -> Callable[[dict], bool]:
    """Filter für Vertretungsplan-Einträge einer Lehrkraft: Einträge eigener Klassen sowie eigene
    (vertritt, wird vertreten, Aufsicht)."""
    own = own_class_ids(user, snap)
    tid = getattr(user, "teacher_id", None)

    def ok(entry: dict) -> bool:
        if tid and tid in (entry.get("teacher"), entry.get("substitute"), entry.get("original_teacher")):
            return True
        return bool(own and set(entry.get("classes") or []) & own)

    return ok


def _mentions(text: str, tokens: Iterable[str]) -> bool:
    for t in tokens:
        if t and re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text or ""):
            return True
    return False


def visible_student_ids(user, snap=None) -> Optional[frozenset[str]]:
    """``None`` = alle Schüler sichtbar; sonst Menge der sichtbaren Schüler-IDs."""
    snap = snap or snapshot()
    if has(user, "students.read") and perm_scope(user, "students.read") is None:
        return None
    out = set(own_student_ids(user))
    if has(user, "students.read") and getattr(user, "teacher_id", None):
        out.update(teacher_student_ids(user.teacher_id, snap))
    if has(user, "students.read") and perm_scope(user, "students.read") == "own_branch":
        classes = own_class_ids(user, snap)
        out.update(s.id for s in snap[1].students if s.class_id in classes)
    return frozenset(out)


def teacher_student_ids(teacher_id: str, snap=None) -> frozenset[str]:
    snap = snap or snapshot()

    def compute():
        classes = teacher_class_ids(teacher_id, snap)
        return frozenset(s.id for s in snap[1].students if s.class_id in classes)

    return cached("teacher_students", (teacher_id,), compute, snap)


def can_see_student(user, student_id: str, snap=None) -> bool:
    vis = visible_student_ids(user, snap)
    return vis is None or student_id in vis


def students_in_scope(user, perm: str, snap=None) -> Optional[frozenset[str]]:
    """Schüler-IDs, für die ``perm`` gilt (``None`` = alle; leere Menge = keine).

    Scopes: ``own_classes`` (Lehrkraft: unterrichtete Klassen), ``own``/``own_children``
    (Schüler/Eltern: ``student_ids``)."""
    if not has(user, perm):
        return frozenset()
    scope = perm_scope(user, perm)
    if scope is None:
        return None
    snap = snap or snapshot()
    if scope == "own_classes":
        tid = getattr(user, "teacher_id", None)
        return teacher_student_ids(tid, snap) if tid else frozenset()
    if scope == "own_branch":   # Abteilungsleitung: eigene Klassen + Klassen des Zweigs
        classes = own_class_ids(user, snap)
        return frozenset(s.id for s in snap[1].students if s.class_id in classes)
    return frozenset(own_student_ids(user))


# ------------------------------------------------------- Vertretungsplan filtern
_PRIVATE_ENTRY_KEYS = ("reason", "absence_reason", "reasons")


def absence_reasons(school: School, day: date) -> list[str]:
    """Gründe von Lehrkraft-Abwesenheiten (personenbezogen → für Nicht-Editoren entfernen).

    Gründe von Klassen-/Raum-Abwesenheiten (z. B. „Klassenfahrt“, „Wasserschaden“) und von entfallendem
    Unterricht (``kind="lesson"``, z. B. „Sporthalle gesperrt“ – betrifft keine Person, die Lehrkraft ist frei)
    bleiben in Hinweistexten sichtbar.
    """
    out = []
    for a in school.absences:
        if a.kind != "teacher":   # class / room / lesson: nicht personenbezogen
            continue
        if a.reason and a.reason.strip():
            try:
                if date.fromisoformat(a.date_from) <= day <= date.fromisoformat(a.date_to):
                    out.append(a.reason.strip())
            except ValueError:
                continue
    # Längere Gründe zuerst ersetzen
    return sorted(set(out), key=len, reverse=True)


def scrub(text: Optional[str], reasons: list[str]) -> Optional[str]:
    """Entfernt Abwesenheitsgründe aus Hinweistexten – nur als ganze Wörter (Grund „Kur“ lässt „Exkursion“,
    „Kurs“ und „Frau Kurz“ unverändert)."""
    if not text or not reasons:
        return text
    out = text
    for r in reasons:
        out = re.sub(rf"(?<!\w){re.escape(r)}(?!\w)", "", out, flags=re.IGNORECASE)
    if out == text:
        return text
    out = re.sub(r"\(\s*[,;:–-]?\s*\)", "", out)
    out = re.sub(r"\s*[:;,–-]\s*$", "", out)
    out = re.sub(r"^\s*[:;,–-]\s*", "", out)
    return re.sub(r"\s{2,}", " ", out).strip()


def _clean_entry(entry: dict, reasons: list[str]) -> dict:
    e = {k: v for k, v in entry.items() if k not in _PRIVATE_ENTRY_KEYS}
    if reasons and e.get("note"):
        e["note"] = scrub(e["note"], reasons)
    return e


def _entry_stats(entries: list[dict]) -> dict:
    out: dict[str, int] = {}
    for e in entries:
        k = e.get("kind") or "?"
        out[k] = out.get(k, 0) + 1
    return out


def pupil_entry_filter(user, snap, student_ids: Optional[list[str]] = None) -> Callable[[dict], bool]:
    """Filter: nur Einträge der eigenen Klasse(n) bzw. gewählten Kursteile
    (``student_ids`` schränkt bei Eltern auf ein Kind ein)."""
    school = snap[1]
    students = index("students", snap)
    selections: list[tuple[str, dict[str, list[int]]]] = []
    for sid in (student_ids if student_ids is not None else own_student_ids(user)):
        st = students.get(sid)
        if st:
            selections.append((st.class_id, student_parts(sid, snap)))
    courses = index("courses", snap)
    lessons = cached("lesson_course", (), lambda: {le.id: le.course_id for le in school.lessons}, snap)

    def ok(entry: dict) -> bool:
        classes = entry.get("classes") or []
        for class_id, parts in selections:
            if class_id not in classes:
                continue
            lid = entry.get("lesson_id")
            cid = lessons.get(lid) if lid else None
            if cid and cid in courses and len(courses[cid].parts) > 1:
                sel = parts.get(cid)
                if sel is not None and entry.get("part") is not None and entry["part"] not in sel:
                    continue
            return True
        return False

    return ok


_PUBLIC_TEACHER_KEYS = {"off": (), "short": ("teacher",), "name": ("teacher", "name")}


def _public_teacher_details(details: list[dict], level: str) -> list[dict]:
    """Abwesende Lehrkräfte für die öffentliche Sicht (``settings.public_absent_teachers``): nur Kürzel bzw.
    Kürzel + Name, nie Grund, Stunden oder Fallzahl."""
    keys = _PUBLIC_TEACHER_KEYS.get(level, _PUBLIC_TEACHER_KEYS["short"])
    return [{k: d.get(k) or "" for k in keys} for d in details] if keys else []


def filter_plan(user, plan: dict, snap, *, site: Optional[str] = None, class_id: Optional[str] = None,
                teacher: Optional[str] = None, public: bool = False) -> dict:
    """Vertretungsplan nach Rolle filtern (gibt eine Kopie zurück).

    * ``substitution.edit``: alles (Gründe bleiben – stehen aber ohnehin nur in ``absences``)
    * ``plans.read_all`` (uneingeschränkt): alles ohne Abwesenheitsgründe
    * Lehrkräfte (``plans.read_all`` → ``own_classes``): nur Einträge eigener Klassen und eigene (vertritt,
      wird vertreten, Aufsicht); abwesende Lehrkräfte (auch ``absent_teacher_details``, Fallzahl aus den
      sichtbaren Einträgen) nur, soweit sie in diesen Einträgen vorkommen; Klassen-Details nur eigene Klassen;
      Warnungen nur, wenn sie eigene Klassen/die eigene Person nennen
    * Schüler/Eltern: nur eigene Klasse/Kurse, keine abwesenden Lehrkräfte (auch keine Details), keine Warnungen
    * ``public=True`` (Monitor, Aushang/Druck): keine Aufsichten, Warnungen und Gründe; ``absent_teachers`` leer,
      ``absent_teacher_details`` laut ``settings.public_absent_teachers`` (``off`` | ``short`` = Kürzel |
      ``name``). Ganze Schule nur mit ``monitor.read`` (bzw. für reine Monitor-Konten), sonst bleibt der
      Datenumfang der Rolle – ``public`` erweitert ihn nie.
    """
    school = snap[1]
    editor = has(user, "substitution.edit")
    reader = has(user, "plans.read_all")
    pupil_role = not reader and bool(own_student_ids(user))
    monitor = has(user, "monitor.read")
    if not (editor or reader or pupil_role or monitor):
        raise HTTPException(403, "Keine Berechtigung")
    if not (editor or reader) and not pupil_role:
        public = True
    whole_school = public and monitor
    pupil = pupil_role and not whole_school
    scoped = not editor and not whole_school and not pupil and is_scoped_teacher(user)
    try:
        day = date.fromisoformat(plan.get("date", ""))
        reasons = [] if editor and not public else absence_reasons(school, day)
    except ValueError:
        reasons = []
    entries = plan.get("entries") or []
    if pupil:
        ok = pupil_entry_filter(user, snap)
        entries = [e for e in entries if e.get("kind") != "aufsicht" and ok(e)]
    elif scoped:
        ok = teacher_entry_filter(user, snap)
        entries = [e for e in entries if ok(e)]
    if public:
        entries = [e for e in entries if e.get("kind") != "aufsicht"]
    if site:
        entries = [e for e in entries if not e.get("site") or e.get("site") == site]
    if class_id:
        entries = [e for e in entries if class_id in (e.get("classes") or [])]
    # Lehrkräfte, die in den sichtbaren Einträgen vorkommen (vor dem Lehrkraft-Filter, damit die Liste der
    # abwesenden Lehrkräfte beim Filtern auf eine Person stehen bleibt)
    seen = {x for e in entries for x in (e.get("teacher"), e.get("substitute")) if x}
    before_teacher = entries   # Grundlage für Fallzahlen und Klassenfilter der Karte (unabhängig von ``teacher``)
    if teacher:
        entries = [e for e in entries if teacher in (e.get("teacher"), e.get("substitute"))]
    out = {k: v for k, v in plan.items() if k != "entries"}
    out["entries"] = [_clean_entry(e, reasons) for e in entries]
    t_details = [dict(d) for d in plan.get("absent_teacher_details") or []]
    c_details = [dict(d) for d in plan.get("absent_class_details") or []]
    if not (pupil or public or scoped) and (site or class_id or teacher):
        out["stats"] = {**(plan.get("stats") or {}), **{"gefiltert": len(out["entries"])}}
    if scoped:
        own = own_class_ids(user, snap)
        tid = getattr(user, "teacher_id", None)
        out["absent_teachers"] = [t for t in plan.get("absent_teachers") or [] if t in seen or t == tid]
        out["absent_classes"] = [c for c in plan.get("absent_classes") or [] if c in own]
        from schulmanager.substitution import absence_cases
        cases = absence_cases(before_teacher)
        t_details = [{**d, "cases": cases.get(d.get("teacher"), 0)} for d in t_details
                     if d.get("teacher") in seen or d.get("teacher") == tid]
        c_details = [d for d in c_details if d.get("class") in own]
        tokens = list(own) + ([tid] if tid else [])
        out["warnings"] = [w for w in plan.get("warnings") or [] if _mentions(w, tokens)]
        out["stats"] = _entry_stats(out["entries"])
    if pupil:
        own = own_class_ids(user, snap)
        out["absent_classes"] = [c for c in plan.get("absent_classes") or [] if c in own]
        c_details = [d for d in c_details if d.get("class") in own]
        t_details = []
    if pupil or public:
        out["absent_teachers"] = []
        out["warnings"] = []
        out["stats"] = _entry_stats(out["entries"])
    if site or class_id:
        classes = school.index("classes")

        def class_ok(c: Optional[str]) -> bool:
            return (not site or not classes.get(c) or classes[c].site in ("", site)) and (not class_id or c == class_id)

        out["absent_classes"] = [c for c in out.get("absent_classes") or [] if class_ok(c)]
        c_details = [d for d in c_details if class_ok(d.get("class"))]
        teachers = school.index("teachers")
        affected = {e.get("teacher") for e in before_teacher} if class_id else None
        t_details = [d for d in t_details
                     if (not site or not teachers.get(d.get("teacher")) or not teachers[d["teacher"]].sites
                         or site in teachers[d["teacher"]].sites)
                     and (affected is None or d.get("teacher") in affected)]
    if public:
        level = getattr(school.settings, "public_absent_teachers", "short")
        if level != "name":
            # Hinweise wie „Vertretung für Frau Busch“ → „Vertretung für BUS“ (öffentlich nur Kürzel)
            names = sorted(((d.get("name"), d.get("teacher")) for d in plan.get("absent_teacher_details") or []
                            if d.get("name") and d.get("teacher")), key=lambda x: len(x[0]), reverse=True)
            for e in out["entries"] if names else ():
                for name, tid in names:
                    if e.get("note") and name in e["note"]:
                        # nur ganze Namen („Frau Lang“ nicht in „Frau Lange“)
                        e["note"] = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", lambda _m, t=tid: t, e["note"])
        t_details = _public_teacher_details(t_details, level)
    out["absent_teacher_details"] = t_details
    out["absent_class_details"] = c_details
    if reasons:
        out["warnings"] = [scrub(w, reasons) for w in out.get("warnings") or []]
    return out


def absences_for_day(school: School, day: date) -> list[dict]:
    out = []
    for a in school.absences:
        try:
            if date.fromisoformat(a.date_from) <= day <= date.fromisoformat(a.date_to):
                out.append(a.to_dict())
        except ValueError:
            continue
    return out


# ----------------------------------------------------------------- Diverses
_ID_BAD = re.compile(r"[/#?\\\x00-\x1f]")


def check_id(value: str) -> str:
    v = (value or "").strip()
    if not v:
        raise HTTPException(422, "Die ID darf nicht leer sein")
    if len(v) > 64 or _ID_BAD.search(v):
        raise HTTPException(422, f"Ungültige ID „{v}“ (max. 64 Zeichen, keine Zeichen / # ? \\)")
    return v


def new_id(existing: Iterable[str], prefix: str) -> str:
    taken = set(existing)
    n = len(taken) + 1
    while f"{prefix}{n}" in taken:
        n += 1
    return f"{prefix}{n}"


def find(items: list, item_id: str, what: str = "Eintrag"):
    for x in items:
        if x.id == item_id:
            return x
    raise HTTPException(404, f"{what} {item_id} nicht gefunden")


def lesson_by_id(school: School, lesson_id: str):
    for le in school.lessons:
        if le.id == lesson_id:
            return le
    return None
