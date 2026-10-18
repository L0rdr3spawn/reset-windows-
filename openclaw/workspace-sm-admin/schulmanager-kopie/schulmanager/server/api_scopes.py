"""API-Zugänge mit Umfang: Bereiche, Filter, zentrale Durchsetzung (docs/API-ZUGAENGE.md).

Ein **Zugang** ist ein ``ApiToken`` mit ``scope`` (Bereiche + Filter + optional Schreibrechte). Er gilt **nur** für die
öffentliche, versionierte API unter ``/api/v1/open/…`` (``routes/api_open.py``) – jede andere Route lehnt
``deps.authenticate`` für solche Zugänge ab. Innerhalb der öffentlichen API gilt:

* Jede Route hängt an einem **Bereich** (:data:`AREAS`) über ``Depends(open_access("<bereich>"))``. Ohne diese
  Abhängigkeit gibt es keine Route (``tests/test_api_access.py`` prüft das für alle Routen unter ``/open``).
* Der Zugang handelt **als sein Konto** (Rechte und Datenumfang des Kontos gelten bei jeder Anfrage neu, der
  Zugang kann also nie mehr als das Konto) – und zusätzlich nur innerhalb der freigegebenen Bereiche und Filter.
* Filter ``classes`` / ``teachers`` / ``rooms`` / ``students`` ergeben zusammen die **erlaubte Menge** (Vereinigung:
  Klasse 5a *oder* Lehrkraft XY); ``sites`` schränkt zusätzlich ein (Und). Kein Filter = alles, was das Konto sieht.
* Gesundheits- und Förderdaten (Krankmeldungen, Atteste, Nachteilsausgleich, Abwesenheitsgründe, Nachschreibtermine
  einzelner Schüler) liefert keine öffentliche Route – :func:`strip_private` entfernt sie zusätzlich aus Antworten,
  die bestehende Handler wiederverwenden.

Neue Funktion ⇒ Bereich festlegen (siehe CLAUDE.md „API-Zugänge als Standard“).
"""
from __future__ import annotations

import ipaddress
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable, Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .db import get_db, utcnow

LOG_KEEP = 200                 # Protokollzeilen je Zugang
DEFAULT_RATE = 60              # Anfragen pro Minute, wenn der Zugang nichts anderes sagt
MAX_RATE = 600
MAX_EXPIRES_DAYS = 365
DEFAULT_EXPIRES_DAYS = 90
MAX_ACCESS_PER_USER = 25
MAX_FILTER_VALUES = 300
TOKEN_PREFIX = "sma_"          # Zugänge mit Umfang (persönliche Tokens: ``smt_``)

FILTER_KINDS = ("classes", "teachers", "rooms", "students", "sites")
FILTER_LABELS = {"classes": "Klassen", "teachers": "Lehrkräfte", "rooms": "Räume", "students": "Schüler/innen",
                 "sites": "Standorte"}

# Bereich → Beschreibung. ``filters``: welche Filter wirken; ``needs``: Rechte des Kontos (eines davon genügt);
# ``write``: Bereich kennt Schreibzugriff. Reihenfolge = Anzeige.
AREAS: dict[str, dict[str, Any]] = {
    "timetable": {
        "label": "Stundenplan", "filters": ["classes", "teachers", "students", "rooms", "sites"],
        "needs": ["plans.read_all", "timetable.edit"],
        "description": "Wochenpläne einer Klasse, Lehrkraft oder eines Schülers (Raumpläne zusätzlich mit Bereich „Räume“)."},
    "substitutions": {
        "label": "Vertretungsplan", "filters": ["classes", "teachers", "rooms", "sites"],
        "needs": ["substitution.read"],
        "description": "Vertretungen, Entfall und Raumänderungen eines Tages oder Zeitraums – ohne Abwesenheitsgründe, "
                       "Aufsichten und interne Warnungen."},
    "calendar": {
        "label": "Termine & Kalender", "filters": ["classes", "teachers", "students", "rooms", "sites"],
        "needs": ["plans.read_all", "timetable.edit"],
        "description": "Schuljahr (Ferien, Wochen) und Kalenderwochen mit Stunden, Terminen und Klausuren – ohne "
                       "Fehlzeiten, Hausaufgaben und Nachschreibtermine."},
    "rooms": {
        "label": "Räume", "filters": ["rooms", "sites"], "needs": ["rooms.read", "timetable.edit"],
        "description": "Liste der Räume mit Standort und Raumpläne (Belegung)."},
    "announcements": {
        "label": "Mitteilungen", "filters": ["classes", "sites"], "needs": [], "write": True,
        "write_needs": ["announcement.post"],
        "description": "Aktuell gültige Mitteilungen (schwarzes Brett), die das Konto sieht – nur für alle oder "
                       "bestimmte Klassen. Optional: neue Mitteilungen veröffentlichen."},
    "directory": {
        "label": "Verzeichnis", "filters": ["classes", "sites"], "needs": ["plans.read_all", "masterdata.read",
                                                                          "timetable.edit"],
        "description": "Klassen, Standorte und Lehrkräfte (Kürzel, Name) als Nachschlageliste – keine Schüler/innen."},
}
# Bereiche, die es bewusst NICHT gibt (für llms.txt und die Oberfläche)
NOT_OFFERED = {
    "messages": "Private Nachrichten (Postfach) und Chats werden nie über API-Zugänge freigegeben.",
    "health": "Krankmeldungen, Atteste, Nachteilsausgleich und Förderdaten werden nie über API-Zugänge freigegeben.",
    "students": "Schülerlisten, Noten, Klassenbuch und Fehlzeiten werden nicht über API-Zugänge freigegeben.",
}
PUBLIC_AREAS = {"meta"}        # Routen ohne Anmeldung (nur Struktur)

_PRIVATE_KEY_PARTS = ("reason", "attendance", "support", "hint", "homework", "diagnos", "makeup", "nachteil")


def strip_private(obj: Any) -> Any:
    """Entfernt rekursiv Schlüssel mit Gesundheits-/Förder-/Fehlzeitenbezug aus einer Antwort (Sicherheitsnetz)."""
    if isinstance(obj, dict):
        return {k: strip_private(v) for k, v in obj.items()
                if not any(p in str(k).lower() for p in _PRIVATE_KEY_PARTS)}
    if isinstance(obj, (list, tuple)):
        return [strip_private(v) for v in obj]
    return obj


# --------------------------------------------------------------------------------------- Filter
@dataclass
class Filters:
    classes: set[str] = field(default_factory=set)
    teachers: set[str] = field(default_factory=set)
    rooms: set[str] = field(default_factory=set)
    students: set[str] = field(default_factory=set)
    sites: set[str] = field(default_factory=set)

    @classmethod
    def from_scope(cls, scope: Optional[dict]) -> "Filters":
        f = (scope or {}).get("filters") or {}
        return cls(**{k: {str(x) for x in (f.get(k) or [])} for k in FILTER_KINDS})

    @property
    def restricted(self) -> bool:
        """Mindestens ein Filter für Klassen/Lehrkräfte/Räume/Schüler gesetzt (Standorte schränken nur zusätzlich ein)."""
        return bool(self.classes or self.teachers or self.rooms or self.students)

    def plan_allowed(self, kind: str, ref: str) -> bool:
        """Darf der Plan ``kind``/``ref`` abgerufen werden? Ohne Filter ja; sonst muss ``ref`` im Filter der Art stehen."""
        if not self.restricted:
            return True
        coll = {"class": self.classes, "teacher": self.teachers, "room": self.rooms, "student": self.students}.get(kind)
        return bool(coll) and ref in coll

    def entry_allowed(self, e: dict, snap=None) -> bool:
        """Vertretungs-Eintrag: Klasse, Lehrkraft (auch Vertretung/Original) oder Raum im Filter; Standort muss passen."""
        if self.sites and e.get("site") and e.get("site") not in self.sites:
            return False
        if not self.restricted:
            return True
        if self.classes and set(e.get("classes") or []) & self.classes:
            return True
        if self.teachers and self.teachers & {e.get("teacher"), e.get("substitute"), e.get("original_teacher")}:
            return True
        if self.rooms and self.rooms & {e.get("room"), e.get("new_room"), e.get("original_room")}:
            return True
        if self.students and snap is not None:
            from .routes.features_common import student_parts
            school = snap[1]
            cls = {s.class_id for s in school.students if s.id in self.students}
            if set(e.get("classes") or []) & cls:
                for sid in self.students:
                    parts = student_parts(sid, snap)
                    if e.get("course_id") in parts and (e.get("part") is None or e.get("part") in parts[e["course_id"]]):
                        return True
        return False


# ------------------------------------------------------------------------------- Zugriffsobjekt
@dataclass
class Access:
    """Ergebnis von :func:`open_access`: das Konto (``user``), der Bereich und die Filter des Zugangs."""
    user: Any
    area: str
    scope: Optional[dict]          # None = Sitzung bzw. persönliches Token (kein Zugang mit Umfang)
    filters: Filters

    @property
    def scoped(self) -> bool:
        return self.scope is not None


def open_access(area: str, *, write: bool = False) -> Callable[..., Access]:
    """Abhängigkeit jeder Route der öffentlichen API: verlangt Anmeldung, den Bereich ``area`` (bei ``write=True``
    zusätzlich als Schreibbereich) und protokolliert die Nutzung. Registriert den Bereich der Route (``_open_area``)."""
    if area not in AREAS:
        raise ValueError(f"Unbekannter API-Bereich: {area}")

    def dependency(request: Request, db: Session = Depends(get_db)) -> Access:
        from .deps import current_user
        user = current_user(request, db)
        scope = getattr(user, "api_scope", None)
        tok_id = getattr(user, "api_token_id", None)
        if scope is not None:
            if area not in (scope.get("areas") or []):
                log_use(db, tok_id, request, area, "area_denied")
                raise HTTPException(403, f"Dieser Zugang umfasst den Bereich „{AREAS[area]['label']}“ nicht.")
            if write and area not in (scope.get("write") or []):
                log_use(db, tok_id, request, area, "write_denied")
                raise HTTPException(403, "Dieser Zugang darf in diesem Bereich nur lesen.")
            log_use(db, tok_id, request, area, "ok")
        return Access(user=user, area=area, scope=scope, filters=Filters.from_scope(scope))

    dependency._open_area = area           # type: ignore[attr-defined]
    dependency._open_write = write         # type: ignore[attr-defined]
    dependency.__name__ = f"open_access_{area}{'_write' if write else ''}"
    return dependency


def public_meta() -> None:
    """Platzhalter-Abhängigkeit für Routen ohne Anmeldung (Struktur-Metadaten)."""
    return None


public_meta._open_area = "meta"            # type: ignore[attr-defined]


def route_area(route: Any) -> Optional[str]:
    """Bereich einer FastAPI-Route (über ihre Abhängigkeiten) oder ``None``."""
    dependant = getattr(route, "dependant", None)
    stack = [dependant] if dependant is not None else []
    while stack:
        d = stack.pop()
        area = getattr(d.call, "_open_area", None)
        if area:
            return area
        stack.extend(d.dependencies)
    return None


def iter_routes(routes: Any, prefix: str = ""):
    """Alle Routen mit vollem Pfad – auch hinter ``include_router`` (neuere FastAPI-Versionen hängen eingebundene
    Router als ``_IncludedRouter`` mit ``include_context.prefix`` in ``app.routes``). Liefert ``(pfad, route)``."""
    for r in routes:
        inner = getattr(r, "original_router", None)
        if inner is not None:
            ctx = getattr(r, "include_context", None)
            yield from iter_routes(inner.routes, prefix + (getattr(ctx, "prefix", "") or ""))
        elif hasattr(r, "path"):
            yield prefix + r.path, r


def open_routes(app: Any) -> list[dict]:
    """Alle Routen der öffentlichen API: ``[{method, path, area, write, summary}]`` (Reihenfolge wie registriert)."""
    out: list[dict] = []
    for path, r in iter_routes(app.routes):
        if not (path.startswith("/api/v1/open") or path.startswith("/api/v1/meta")):
            continue
        for m in sorted(getattr(r, "methods", None) or []):
            if m in ("HEAD", "OPTIONS"):
                continue
            write = False
            dep = getattr(r, "dependant", None)
            stack = [dep] if dep is not None else []
            while stack:
                d = stack.pop()
                if getattr(d.call, "_open_write", False):
                    write = True
                stack.extend(d.dependencies)
            out.append({"method": m, "path": path, "area": route_area(r), "write": write,
                        "summary": getattr(r, "summary", None) or getattr(r, "name", ""),
                        "description": (getattr(r, "description", "") or "").strip()})
    return out


# ------------------------------------------------------------------ Durchsetzung (von deps.authenticate)
_rate_lock = threading.Lock()
_rate_hits: dict[Any, deque] = defaultdict(deque)


def reset_rate_limits() -> None:
    with _rate_lock:
        _rate_hits.clear()


def _rate_ok(token_id: Any, limit: int) -> tuple[bool, int]:
    now = time.monotonic()
    with _rate_lock:
        q = _rate_hits[token_id]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            return False, max(1, int(60 - (now - q[0])) + 1)
        q.append(now)
        return True, 0


def ip_allowed(ip: Optional[str], allow: Optional[list[str]]) -> bool:
    if not allow:
        return True
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False
    for entry in allow:
        try:
            if addr in ipaddress.ip_network(entry.strip(), strict=False):
                return True
        except ValueError:
            continue
    return False


def log_use(db: Session, token_id: Optional[int], request: Request, area: str, outcome: str) -> None:
    """Nutzungsprotokoll (letzte :data:`LOG_KEEP` Zeilen je Zugang); Fehler hier brechen nie die Anfrage ab."""
    if not token_id:
        return
    try:
        from .deps import _api_path, client_ip
        from .db_models import ApiToken
        from .feature_models.api_access import ApiTokenLog
        db.add(ApiTokenLog(token_id=token_id, at=utcnow(), method=request.method, path=_api_path(request)[:200],
                           area=area, outcome=outcome, ip=client_ip(request)))
        if outcome == "ok":
            row = db.get(ApiToken, token_id)
            if row is not None:
                row.use_count = (row.use_count or 0) + 1
        db.flush()
        old = db.scalars(select(ApiTokenLog.id).where(ApiTokenLog.token_id == token_id)
                         .order_by(ApiTokenLog.id.desc()).offset(LOG_KEEP)).all()
        if old:
            db.execute(delete(ApiTokenLog).where(ApiTokenLog.id.in_(old)))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()


def check_request(request: Request, db: Session, row: Any) -> None:
    """Zentrale Vorprüfung für Zugänge mit Umfang (in ``deps.authenticate``): nur ``/open/…``, IP-Beschränkung,
    Ratenlimit. Wirft 403/429."""
    from .deps import _api_path, client_ip
    path = _api_path(request)
    if not (path == "/open" or path.startswith("/open/")):
        log_use(db, row.id, request, "", "not_open_api")
        raise HTTPException(403, "Dieser Zugang gilt nur für die öffentliche API (/api/v1/open/…).")
    if not ip_allowed(client_ip(request), row.ip_allow):
        log_use(db, row.id, request, "", "ip_denied")
        raise HTTPException(403, "Von dieser Adresse ist der Zugang nicht freigegeben.")
    limit = min(MAX_RATE, row.rate_limit or DEFAULT_RATE)
    ok, retry = _rate_ok((row.id, (row.token_hash or "")[:12]), limit)
    if not ok:
        log_use(db, row.id, request, "", "rate_limited")
        raise HTTPException(429, f"Zu viele Anfragen (höchstens {limit} pro Minute).", headers={"Retry-After": str(retry)})


# ----------------------------------------------------------------- Anlegen: was darf das Konto freigeben?
def area_available(user, area: str) -> bool:
    """Darf das Konto ``user`` den Bereich überhaupt freigeben (Rechte des Kontos)?"""
    needs = AREAS[area]["needs"]
    return not needs or any(p in user.permissions for p in needs)


def write_available(user, area: str) -> bool:
    meta = AREAS[area]
    return bool(meta.get("write")) and any(p in user.permissions for p in meta.get("write_needs") or [])


def creatable_values(user, snap) -> dict[str, Optional[list[str]]]:
    """Werte je Filterart, die das Konto freigeben darf (``None`` = alle der Schule). Nie mehr als das Konto selbst
    sieht: Klassen laut Planzugriff, fremde Lehrkräfte/Räume nur mit uneingeschränktem Planzugriff, Schüler/innen nur
    sichtbare."""
    from .routes import features_common as fc
    all_plans = fc.reads_all_plans(user) or fc.has(user, "timetable.edit")
    classes = fc.plan_class_ids(user, snap)
    out: dict[str, Optional[list[str]]] = {
        "classes": None if classes is None else sorted(classes),
        "teachers": None if all_plans else ([user.teacher_id] if getattr(user, "teacher_id", None) else []),
        "rooms": None if (all_plans or fc.has(user, "rooms.read")) else [],
        "sites": None,
    }
    if fc.has(user, "students.read"):
        vis = fc.visible_student_ids(user, snap)
        out["students"] = None if vis is None else sorted(vis)
    else:
        out["students"] = []
    return out


def normalize_scope(user, snap, *, areas: list[str], write: list[str], filters: dict[str, list[str]]) -> dict:
    """Prüft die Wünsche beim Anlegen gegen die Rechte des Kontos und liefert den gespeicherten ``scope``.
    Wirft 422 (unbekannt) bzw. 403 (mehr als das Konto sieht)."""
    areas = list(dict.fromkeys(areas))
    if not areas:
        raise HTTPException(422, "Bitte mindestens einen Bereich auswählen.")
    for a in areas:
        if a not in AREAS:
            raise HTTPException(422, f"Unbekannter Bereich: {a}")
        if not area_available(user, a):
            raise HTTPException(403, f"Der Bereich „{AREAS[a]['label']}“ darf mit diesem Konto nicht freigegeben "
                                     "werden (fehlendes Recht).")
    write = list(dict.fromkeys(write))
    for a in write:
        if a not in areas:
            raise HTTPException(422, f"Schreibrecht „{a}“ gehört zu keinem gewählten Bereich.")
        if not write_available(user, a):
            raise HTTPException(403, f"Schreibzugriff im Bereich „{AREAS.get(a, {}).get('label', a)}“ ist mit diesem "
                                     "Konto nicht möglich.")
    allowed = creatable_values(user, snap)
    school = snap[1]
    known = {"classes": {c.id for c in school.classes}, "teachers": {t.id for t in school.teachers},
             "rooms": {r.id for r in school.rooms}, "students": {s.id for s in school.students},
             "sites": {s.id for s in school.sites}}
    clean: dict[str, list[str]] = {}
    for kind in FILTER_KINDS:
        vals = list(dict.fromkeys(str(v) for v in (filters.get(kind) or [])))
        if len(vals) > MAX_FILTER_VALUES:
            raise HTTPException(422, f"Zu viele Einträge bei „{FILTER_LABELS[kind]}“ (höchstens {MAX_FILTER_VALUES}).")
        unknown = [v for v in vals if v not in known[kind]]
        if unknown:
            raise HTTPException(422, f"Unbekannt bei „{FILTER_LABELS[kind]}“: {', '.join(unknown[:5])}")
        permitted = allowed.get(kind)
        if permitted is not None:
            foreign = [v for v in vals if v not in permitted]
            if foreign:
                raise HTTPException(403, f"Bei „{FILTER_LABELS[kind]}“ nur Einträge, die Sie selbst sehen dürfen "
                                         f"(nicht erlaubt: {', '.join(foreign[:5])}).")
        if vals:
            clean[kind] = vals
    # Ohne Filter dürfen eingeschränkte Konten nur ihren eigenen Umfang ausgeben – das erzwingt jede Anfrage über
    # die Rechte des Kontos; zusätzlich Hinweis im Vorschautext.
    return {"areas": areas, "write": write, "filters": clean}


# ------------------------------------------------------------------------------- Beschreibung
def _names(school, kind: str, ids: list[str]) -> list[str]:
    coll = {"classes": "classes", "teachers": "teachers", "rooms": "rooms", "students": None, "sites": "sites"}[kind]
    if coll is None:
        return [f"{len(ids)} Schüler/in(nen)"] if ids else []
    idx = school.index(coll)
    out = []
    for i in ids:
        obj = idx.get(i)
        name = getattr(obj, "name", "") if obj else ""
        out.append(f"{i} ({name})" if name and name != i else i)
    return out


def describe(scope: dict, school, user=None) -> dict[str, Any]:
    """„Dieser Zugang darf: …“ für die Oberfläche: ``{can: [...], cannot: [...], warnings: [...]}``."""
    f = scope.get("filters") or {}
    can: list[str] = []
    for a in scope.get("areas") or []:
        meta = AREAS[a]
        rel = [k for k in meta["filters"] if f.get(k)]
        line = f"{meta['label']} lesen"
        if rel:
            line += " – nur für " + "; ".join(f"{FILTER_LABELS[k]}: {', '.join(_names(school, k, f[k]))}" for k in rel)
        else:
            line += " – alles, was das Konto sieht"
        can.append(line)
        if a in (scope.get("write") or []):
            can.append(f"{meta['label']}: neue Einträge anlegen")
    ignored = [k for k in FILTER_KINDS if f.get(k) and not any(k in AREAS[a]["filters"] for a in scope.get("areas") or [])]
    cannot = ["Keine Gesundheits-, Förder- oder Fehlzeitendaten", "Keine privaten Nachrichten und Chats",
              "Keine Konten, Passwörter oder Einstellungen", "Keine Änderungen außer den oben genannten"]
    warnings: list[str] = []
    if f.get("students"):
        warnings.append("Schülerpläne sind personenbezogene Daten – nur an Anwendungen weitergeben, die dafür zugelassen sind.")
    if "teachers" in (f or {}) or "directory" in (scope.get("areas") or []):
        warnings.append("Namen von Lehrkräften werden ausgegeben.")
    for k in ignored:
        warnings.append(f"Der Filter „{FILTER_LABELS[k]}“ wirkt in den gewählten Bereichen nicht.")
    if (f.get("sites") and not any(f.get(k) for k in ("classes", "teachers", "rooms", "students"))):
        warnings.append("Nur Standort-Filter: Pläne einzelner Klassen/Lehrkräfte sind dann alle dieses Standorts abrufbar.")
    return {"can": can, "cannot": cannot, "warnings": warnings}


def example_paths(scope: dict) -> list[str]:
    """Beispielaufrufe (Pfad ab ``/api/v1``) passend zum Umfang."""
    f = scope.get("filters") or {}
    first = lambda k, d: (f.get(k) or [d])[0]  # noqa: E731
    paths = {
        "timetable": (f"/open/timetable/class/{first('classes', '5a')}" if f.get("classes") or not f.get("teachers")
                      else f"/open/timetable/teacher/{first('teachers', 'MUS')}"),
        "substitutions": "/open/substitutions",
        "calendar": "/open/calendar/school-year",
        "rooms": "/open/rooms",
        "announcements": "/open/announcements",
        "directory": "/open/classes",
    }
    return [paths[a] for a in scope.get("areas") or [] if a in paths]


def expires_at(days: int):
    return utcnow() + timedelta(days=days)
