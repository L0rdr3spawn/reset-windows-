"""Plan prüfen: Vorschlagspakete berechnen, zustellen und entscheiden (Doku: ``docs/PLAN-PRUEFUNG.md``).

Ablauf
------
1. Die Dauerprüfung (``autoplan.AutoPlanner``) meldet eine neue Problemlage → :func:`start_package` legt ein Paket
   (Status ``berechnung``) mit den Varianten *minimal*, *lokal*, *gründlich* (Generator-Läufe nacheinander im
   Hintergrund, Job-Art ``proposal``) und – wenn nur Lehrkräfte fehlen – *Vertretung statt Planänderung* an.
   Reine Raum-/Aufräumfälle ergeben sofort die Variante *Räume anpassen* (kein Generator).
2. Jedes Ergebnis wird gegen den aktuellen Plan verglichen (:mod:`schulmanager.plan_proposals`): Kennzahlen
   vorher/nachher, Änderungsliste, betroffene Klassen/Lehrkräfte, Unterschied (``diff``). Keine Verbesserung = keine
   Variante. Sind alle fertig, wird das Paket ``offen`` und die Berechtigten erhalten einen Live-Hinweis.
3. Ein neues Paket ersetzt veraltete (``ersetzt``); verschwindet das Problem, werden offene Pakete ``erledigt``.
4. :func:`accept` übernimmt eine Variante **nur**, wenn Plan und Problemlage seit der Berechnung unverändert sind
   (``state_hash``), sonst ``veraltet`` und Neuberechnung. Die Übernahme ist eine normale Version (Scope
   ``timetable``/``autoplan``/``proposals``, rückgängig über „Verlauf & Audit“); betroffene Lehrkräfte werden
   informiert (E-Mail-Ausgang, Live-Ereignis).
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy import select

from .config import config
from .db import SessionLocal, iso, utcnow
from .feature_models.plan_proposals import PlanProposal, PlanProposalLog, PlanProposalVariant

log = logging.getLogger("schulmanager.proposals")

JOB_KIND = "proposal"
OPEN_STATES = ("berechnung", "offen")
RETRY_SECONDS = 3.0
MAX_RETRIES = 60
TRIGGER_LABELS = {
    "teachers": "Lehrkräfte geändert", "rooms": "Räume geändert", "classes": "Klassen geändert",
    "courses": "Kurse geändert", "curricula": "Stundentafeln geändert", "subjects": "Fächer geändert",
    "settings": "Einstellungen geändert", "sites": "Standorte geändert", "timetable": "Stundenplan geändert",
    "lessons": "Stunden geändert", "import": "Import",
}


class ProposalError(Exception):
    """Fehler beim Entscheiden (``status`` = HTTP-Status)."""

    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


def _store():
    from .store import get_store
    return get_store()


def _changed() -> None:
    try:
        from .events import bus
        bus.publish("change", {"version": _store().version, "scope": ["proposals"], "dates": []})
    except Exception:  # pragma: no cover
        pass


def _log(db, package_id: int, action: str, user: Any = None, variant_id: Optional[int] = None,
         note: Optional[str] = None, detail: Optional[dict] = None) -> None:
    db.add(PlanProposalLog(package_id=package_id, action=action, actor_id=getattr(user, "id", None),
                           actor_name=(getattr(user, "display_name", None) or getattr(user, "username", "")
                                       if user is not None else "System"),
                           variant_id=variant_id, note=(note or None) and note[:500], detail=detail or None))


# =================================================================== Ausgabe
def variant_dict(v: PlanProposalVariant, with_diff: bool = False) -> dict:
    out = {"id": v.id, "package_id": v.package_id, "key": v.key, "position": v.position, "title": v.title,
           "description": v.description, "status": v.status, "metrics_before": v.metrics_before or {},
           "metrics_after": v.metrics_after or {}, "changes": v.changes or [],
           "affected_classes": v.affected_classes or [], "affected_teachers": v.affected_teachers or [],
           "moved_lessons": v.moved_lessons, "remaining": v.remaining or [], "valid_from": v.valid_from,
           "compute_seconds": round(float(v.compute_seconds or 0), 1),
           "diff_size": len((v.diff or {}).get("upsert", [])) + len((v.diff or {}).get("delete", []))}
    if with_diff:
        out["diff"] = v.diff or {}
    return out


def package_dict(db, p: PlanProposal, variants: bool = True, log_rows: bool = False) -> dict:
    out = {"id": p.id, "status": p.status, "title": p.title, "created_at": iso(p.created_at),
           "updated_at": iso(p.updated_at), "base_version": p.base_version, "reasons": p.reasons or [],
           "trigger_scope": p.trigger_scope or [],
           "trigger_labels": [TRIGGER_LABELS.get(s, s) for s in (p.trigger_scope or []) if s in TRIGGER_LABELS],
           "problem_count": p.problem_count, "valid_from": p.valid_from, "postponed_until": iso(p.postponed_until),
           "postponed_by": p.postponed_by, "decided_at": iso(p.decided_at), "decided_by": p.decided_by,
           "decision_note": p.decision_note, "chosen_variant_id": p.chosen_variant_id,
           "applied_version": p.applied_version, "informed": p.informed or []}
    if variants:
        rows = db.scalars(select(PlanProposalVariant).where(PlanProposalVariant.package_id == p.id)
                          .order_by(PlanProposalVariant.position, PlanProposalVariant.id)).all()
        out["variants"] = [variant_dict(v) for v in rows if v.status != "entfernt"]
    if log_rows:
        rows = db.scalars(select(PlanProposalLog).where(PlanProposalLog.package_id == p.id)
                          .order_by(PlanProposalLog.id)).all()
        out["log"] = [{"at": iso(r.at), "action": r.action, "actor": r.actor_name, "variant_id": r.variant_id,
                       "note": r.note, "detail": r.detail or {}} for r in rows]
    return out


def list_open() -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(select(PlanProposal).where(PlanProposal.status.in_(OPEN_STATES))
                          .order_by(PlanProposal.id.desc())).all()
        return [package_dict(db, p) for p in rows]


def list_recent(limit: int = 10) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(select(PlanProposal).where(PlanProposal.status.notin_(OPEN_STATES))
                          .order_by(PlanProposal.id.desc()).limit(limit)).all()
        return [package_dict(db, p, variants=False) for p in rows]


def get_package(package_id: int, with_log: bool = False) -> Optional[dict]:
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        return package_dict(db, p, log_rows=with_log) if p else None


def summary() -> dict:
    """Zähler für Badge/Kachel: offene (nicht zurückgestellte) Pakete, zurückgestellte, laufende Berechnung."""
    now = utcnow()
    with SessionLocal() as db:
        rows = db.scalars(select(PlanProposal).where(PlanProposal.status.in_(OPEN_STATES))
                          .order_by(PlanProposal.id.desc())).all()
        ready = [p for p in rows if p.status == "offen" and not (p.postponed_until and p.postponed_until > now)]
        postponed = [p for p in rows if p.status == "offen" and p.postponed_until and p.postponed_until > now]
        computing = [p for p in rows if p.status == "berechnung"]
        newest = ready[0] if ready else None
        return {"open": len(ready), "postponed": len(postponed), "computing": len(computing),
                "newest": {"id": newest.id, "title": newest.title, "created_at": iso(newest.created_at),
                           "problem_count": newest.problem_count} if newest else None,
                "builder": builder.state()}


def find_for_state(state: str) -> Optional[PlanProposal]:
    with SessionLocal() as db:
        return db.scalar(select(PlanProposal).where(PlanProposal.state_hash == state,
                                                    PlanProposal.status.in_(OPEN_STATES))
                         .order_by(PlanProposal.id.desc()).limit(1))


def is_covered(signature: str) -> bool:
    """Wurde genau diese Problemlage schon mit „Vertretung statt Planänderung“ entschieden?"""
    with SessionLocal() as db:
        row = db.scalar(select(PlanProposal).where(PlanProposal.signature == signature,
                                                   PlanProposal.status == "angenommen")
                        .order_by(PlanProposal.id.desc()).limit(1))
        if row is None or row.chosen_variant_id is None:
            return False
        v = db.get(PlanProposalVariant, row.chosen_variant_id)
        return v is not None and v.key == "vertretung"


# =================================================================== Pakete schließen / ersetzen
def _close(db, p: PlanProposal, status: str, note: str = "", user: Any = None, action: Optional[str] = None) -> None:
    p.status, p.updated_at = status, utcnow()
    if status in ("ersetzt", "erledigt", "veraltet", "verworfen"):
        for v in db.scalars(select(PlanProposalVariant).where(PlanProposalVariant.package_id == p.id)):
            v.diff = None            # Rechenergebnis wird nicht mehr gebraucht (spart Platz)
    _log(db, p.id, action or status, user, note=note)


def supersede_others(keep_state: Optional[str]) -> int:
    """Offene Pakete mit anderem Stand → ``ersetzt`` (laufende Berechnung wird abgebrochen)."""
    n = 0
    with SessionLocal() as db:
        for p in db.scalars(select(PlanProposal).where(PlanProposal.status.in_(OPEN_STATES))):
            if keep_state and p.state_hash == keep_state:
                continue
            _close(db, p, "ersetzt", "Der Plan hat sich geändert – neu berechnet")
            n += 1
        db.commit()
    if n:
        builder.cancel(keep_state)
        _changed()
    return n


def close_obsolete() -> int:
    """Es gibt keine Probleme mehr → offene Pakete sind ``erledigt``."""
    n = 0
    with SessionLocal() as db:
        for p in db.scalars(select(PlanProposal).where(PlanProposal.status.in_(OPEN_STATES))):
            _close(db, p, "erledigt", "Das Problem besteht nicht mehr")
            n += 1
        db.commit()
    if n:
        builder.cancel(None)
        _changed()
    return n


def reset_stale() -> None:
    """Nach einem Neustart: halb berechnete Pakete verwerfen (die Prüfung legt sie bei Bedarf neu an)."""
    try:
        with SessionLocal() as db:
            for p in db.scalars(select(PlanProposal).where(PlanProposal.status == "berechnung")):
                _close(db, p, "fehlgeschlagen", "Server wurde neu gestartet")
            db.commit()
    except Exception:  # noqa: BLE001 - z. B. Tabelle fehlt (Altbestand)
        log.debug("Pakete konnten nicht zurückgesetzt werden", exc_info=True)


# =================================================================== Berechnung
class Builder:
    """Rechnet die Varianten des gerade neuesten Pakets nacheinander (ein Generator-Job gleichzeitig)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.active: Optional[dict[str, Any]] = None

    def state(self) -> Optional[dict]:
        with self._lock:
            a = self.active
            if not a:
                return None
            return {"package_id": a["package_id"], "done": a["done"], "total": a["total"], "job_id": a.get("job_id")}

    @property
    def busy(self) -> bool:
        return self.active is not None

    def cancel(self, keep_state: Optional[str]) -> None:
        with self._lock:
            a = self.active
            if not a or (keep_state and a["state"] == keep_state):
                return
            self.active = None
            job_id = a.get("job_id")
            timer = a.get("timer")
        if timer is not None:
            timer.cancel()
        if job_id:
            from .jobs import JobError, manager
            try:
                manager.cancel(job_id)
            except JobError:
                pass

    # ------------------------------------------------------------------ Start
    def start(self, package_id: int, state: str, base, plan, version: int, queue: list, before: dict) -> None:
        with self._lock:
            self.active = {"package_id": package_id, "state": state, "base": base, "plan": plan, "version": version,
                           "queue": list(queue), "before": before, "done": 0, "total": len(queue), "seen_free": [],
                           "retries": 0, "job_id": None, "timer": None, "ready": 0}
        self._next()

    def _next(self) -> None:
        from schulmanager.plan_proposals import free_courses_for
        from .jobs import JobError, _pin_foreign_lessons, manager
        from schulmanager.models import School

        with self._lock:
            a = self.active
            if a is None:
                return
            while a["queue"]:
                item = a["queue"][0]
                spec = item["spec"]
                free = free_courses_for(a["plan"].school, a["plan"].free_courses, spec.scope)
                if free in a["seen_free"] and spec.scope != "wide":
                    a["queue"].pop(0)
                    a["done"] += 1
                    _drop_variant(item["variant_id"])
                    continue
                work = School.from_dict(a["plan"].school.to_dict())
                pinned = _pin_foreign_lessons(work, set(free))
                limit = max(1.0, float(config.autoplan_time_limit or 15) * spec.time_factor)
                params = {"time_limit": limit, "keep_locked": True, "seed": spec.seed, "workers": 1,
                          "free_courses": len(free), "variant": spec.key, "package_id": a["package_id"]}
                context = {"school": a["plan"].school.to_dict(), "free_courses": free, "pinned": pinned,
                           "package_id": a["package_id"], "variant_id": item["variant_id"], "variant_key": spec.key,
                           "started": time.time()}
                try:
                    job = manager.start_generate(work.to_dict(), params, user=None, base_version=a["version"],
                                                 kind=JOB_KIND, context=context)
                except JobError:
                    a["retries"] += 1
                    if a["retries"] > MAX_RETRIES:
                        self._finish(a, "Der Generator war dauerhaft belegt")
                        return
                    t = threading.Timer(RETRY_SECONDS, self._next)
                    t.daemon = True
                    a["timer"] = t
                    t.start()
                    return
                job.user_name = "Plan prüfen"
                a["job_id"], a["current_free"] = job.id, free
                return
            # Warteschlange leer
            self._finish(a, "")

    # ------------------------------------------------------------------ Ergebnis eines Jobs
    def job_finished(self, job) -> None:
        try:
            self._job_finished(job)
        except Exception:  # noqa: BLE001
            log.exception("Plan prüfen: Auswertung fehlgeschlagen")
            with self._lock:
                a = self.active
            if a is not None and a.get("package_id") == job.context.get("package_id"):
                with self._lock:
                    if a["queue"]:
                        a["queue"].pop(0)
                    a["done"] += 1
                self._next()

    def _job_finished(self, job) -> None:
        with self._lock:
            a = self.active
            if a is None or a.get("package_id") != job.context.get("package_id") or a.get("job_id") != job.id:
                return                        # abgebrochen oder ersetzt
            item = a["queue"].pop(0)
            a["done"] += 1
            a["job_id"] = None
            free = a.get("current_free", [])
        spec = item["spec"]
        if job.status == "done" and job.result is not None:
            a["seen_free"].append(free)
            self._store_result(a, item, spec, job)
        else:
            _set_variant(item["variant_id"], status="fehlgeschlagen")
        self._next()

    def _store_result(self, a: dict, item: dict, spec, job) -> None:
        from schulmanager import plan_proposals as pp
        from schulmanager.autoplan import find_problems
        from schulmanager.models import Lesson, School

        base, before = a["base"], a["before"]
        merged = [Lesson.from_dict(d) for d in job.result.get("lessons", [])]
        diff = pp.diff_lessons(base.lessons, merged)
        result = School.from_dict(base.to_dict())
        pp.apply_diff(result, diff)
        after_problems = find_problems(result)
        after = pp.metrics(result, after_problems)
        seconds = round(time.time() - job.context.get("started", time.time()), 1)
        if not (diff["upsert"] or diff["delete"]):
            _set_variant(item["variant_id"], status="keine_loesung")
            return
        if after["problems"] >= before["problems"] or after["conflicts"] > before["conflicts"]:
            _set_variant(item["variant_id"], status="keine_loesung", metrics_after=after, compute_seconds=seconds)
            return
        changes = pp.describe_changes(base, result)
        classes, teachers = pp.affected(changes)
        with SessionLocal() as db:
            same = db.scalars(select(PlanProposalVariant).where(PlanProposalVariant.package_id == a["package_id"],
                                                                PlanProposalVariant.status == "bereit")).all()
            if any(v.diff == diff for v in same):
                _set_variant(item["variant_id"], status="entfernt")
                return
        a["ready"] += 1
        _set_variant(item["variant_id"], status="bereit", metrics_before=before, metrics_after=after, changes=changes,
                     affected_classes=classes, affected_teachers=teachers, moved_lessons=pp.count_moved(changes),
                     remaining=after_problems.summary(result), diff=diff, compute_seconds=seconds)

    # ------------------------------------------------------------------ Abschluss
    def _finish(self, a: dict, error: str) -> None:
        self.active = None
        pid = a["package_id"]
        finish_package(pid, error)


def _drop_variant(variant_id: int) -> None:
    _set_variant(variant_id, status="entfernt")


def _set_variant(variant_id: int, **fields) -> None:
    with SessionLocal() as db:
        v = db.get(PlanProposalVariant, variant_id)
        if v is None:
            return
        for k, val in fields.items():
            setattr(v, k, val)
        db.commit()


builder = Builder()


def finish_package(package_id: int, error: str = "") -> None:
    """Alle Varianten gerechnet: Paket ``offen`` (mindestens eine bereit) oder ``fehlgeschlagen``."""
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        if p is None or p.status != "berechnung":
            return
        ready = db.scalars(select(PlanProposalVariant).where(PlanProposalVariant.package_id == package_id,
                                                             PlanProposalVariant.status == "bereit")).all()
        for v in db.scalars(select(PlanProposalVariant).where(PlanProposalVariant.package_id == package_id,
                                                              PlanProposalVariant.status != "bereit")):
            if v.status in ("berechnung", "keine_loesung", "fehlgeschlagen"):
                v.status = "entfernt"
        if ready:
            p.status, p.updated_at = "offen", utcnow()
            _log(db, p.id, "bereit", note=f"{len(ready)} Variante(n)")
        else:
            _close(db, p, "fehlgeschlagen", error or "Keine bessere Lösung gefunden", action="keine_loesung")
        db.commit()
        ok = bool(ready)
    try:
        from .autoplan import planner
        planner.proposal_ready(package_id, ok)
    except Exception:  # noqa: BLE001
        log.exception("Plan prüfen: Status konnte nicht gemeldet werden")
    if ok:  # Glocke: neuer Vorschlag für Planende
        from . import notification_hooks
        notification_hooks.plan_proposal_ready(package_id)
    _changed()


# =================================================================== Pakete anlegen
def _title(problems: list[str], scopes: list[str], count: int) -> str:
    labels = [TRIGGER_LABELS[s] for s in scopes if s in TRIGGER_LABELS]
    head = f"{count} Problem{'e' if count != 1 else ''} im Stundenplan"
    return head + (f" – {labels[0]}" if labels else "")


def _create_package(db, state: str, signature: str, version: int, reasons: list[str], scopes: list[str], count: int,
                    valid_from: Optional[str]) -> PlanProposal:
    p = PlanProposal(status="berechnung", base_version=version, state_hash=state, signature=signature,
                     title=_title(reasons, scopes, count), reasons=list(reasons), trigger_scope=list(scopes),
                     problem_count=count, valid_from=valid_from)
    db.add(p)
    db.flush()
    _log(db, p.id, "erzeugt", note=p.title, detail={"scope": scopes})
    return p


def start_package(base, plan, version: int, problems: list[str], scopes: list[str]) -> int:
    """Legt das Paket samt Varianten an und startet die Berechnung. ``base`` = Stundenplan, ``plan`` = RepairPlan."""
    from schulmanager import plan_proposals as pp

    state = pp.state_hash(base, plan.before)
    before = pp.metrics(base, plan.before)
    valid_from = pp.valid_from_hint(base, plan.before)
    cover = pp.substitution_cover(base, plan.before)
    supersede_others(state)
    with SessionLocal() as db:
        p = _create_package(db, state, plan.before.signature(), version, problems, scopes, plan.before.count(),
                            valid_from)
        queue = []
        position = 0
        if not plan.free_courses:
            rooms_school = plan.school
            diff = pp.diff_lessons(base.lessons, rooms_school.lessons)
            changes = pp.describe_changes(base, rooms_school)
            classes, teachers = pp.affected(changes)
            after = pp.metrics(rooms_school, plan.after)
            n_rooms = len(plan.room_changes)
            n_orphans = len(plan.removed_orphans)
            parts = []
            if n_rooms:
                parts.append(f"{n_rooms} Raumwechsel")
            if n_orphans:
                parts.append(f"{n_orphans} Stunde(n) ohne Kurs entfernen")
            db.add(PlanProposalVariant(
                package_id=p.id, key="raeume", position=0, title="Räume anpassen – Stunden bleiben, wo sie sind",
                description=" und ".join(parts) + ". Kein Unterricht wird verschoben.", status="bereit",
                metrics_before=before, metrics_after=after, changes=changes, affected_classes=classes,
                affected_teachers=teachers, moved_lessons=0, remaining=plan.after.summary(rooms_school),
                valid_from=valid_from, diff=diff))
            position = 1
        else:
            for spec in pp.variant_specs():
                v = PlanProposalVariant(package_id=p.id, key=spec.key, position=position, title=spec.title,
                                        description=spec.description, status="berechnung", valid_from=valid_from)
                db.add(v)
                db.flush()
                queue.append({"spec": spec, "variant_id": v.id})
                position += 1
        if cover:
            teachers = sorted({t for c in cover for t in c["teachers"]})
            classes = sorted({k for c in cover for k in c["classes"]})
            changes = [{"course_id": c["course_id"], "label": c["label"], "classes": c["classes"],
                        "teachers": c["teachers"], "from": [], "to": [], "rooms": [],
                        "cover": f"{c['where']} wird vertreten ({c['reason']})"} for c in cover][:200]
            db.add(PlanProposalVariant(
                package_id=p.id, key="vertretung", position=position, title="Vertretung statt Planänderung",
                description=(f"Der Stundenplan bleibt unverändert; die {len(cover)} betroffenen Stunde(n) werden in der "
                             "Vertretungsplanung abgedeckt. Sinnvoll, wenn der Anlass nur zeitweise gilt."),
                status="bereit", metrics_before=before, metrics_after=before, changes=changes,
                affected_classes=classes, affected_teachers=teachers, moved_lessons=0,
                remaining=plan.before.summary(base), valid_from=valid_from, diff={"upsert": [], "delete": []}))
        pid = p.id
        db.commit()
    _changed()
    if queue:
        builder.start(pid, state, base, plan, version, queue, before)
    else:
        finish_package(pid)
    return pid


# =================================================================== Entscheiden
def _user_name(user: Any) -> str:
    return getattr(user, "display_name", None) or getattr(user, "username", "") or "System"


def accept(package_id: int, variant_id: int, user: Any, note: str = "") -> dict:
    """„Wir nehmen diesen Plan“: übernimmt die Variante, wenn Plan und Problemlage unverändert sind."""
    from schulmanager import plan_proposals as pp
    from schulmanager.autoplan import find_problems
    from schulmanager.timetable import validate_school

    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        v = db.get(PlanProposalVariant, variant_id)
        if p is None or v is None or v.package_id != p.id or v.status != "bereit":
            raise ProposalError("Vorschlag nicht gefunden", 404)
        if p.status != "offen":
            raise ProposalError("Über dieses Paket wurde schon entschieden" if p.status == "angenommen"
                                else "Dieser Vorschlag ist nicht mehr offen")
        state, key, diff = p.state_hash, v.key, dict(v.diff or {})
        expected = int((v.metrics_after or {}).get("problems", 0))
        title = v.title
        changes, teachers = list(v.changes or []), list(v.affected_teachers or [])

    store = _store()
    info: dict[str, Any] = {}

    class _Stale(Exception):
        pass

    def fn(school):
        if pp.state_hash(school) != state:
            raise _Stale()
        before_conf = validate_school(school)["stats"]["conflicts"]
        if key != "vertretung":
            pp.apply_diff(school, diff)
            after = find_problems(school)
            if validate_school(school)["stats"]["conflicts"] > before_conf or after.count() > expected:
                raise ProposalError("Die Übernahme würde neue Probleme erzeugen – bitte neu berechnen lassen")
            info["remaining"] = after.count()
        return info

    msg = f"Plan-Vorschlag angenommen: {title} ({len(changes)} Kurs(e))"[:480]
    if key == "vertretung":
        if pp.state_hash(store.school) != state:
            _mark_stale(package_id)
            raise ProposalError("Der Plan hat sich seit der Berechnung geändert – der Vorschlag ist veraltet und wird "
                                "neu berechnet.")
    else:
        try:
            store.mutate(user, msg, fn, scope=["timetable", "autoplan", "proposals"], action="plan.proposal_accept",
                         details={"package": package_id, "variant": variant_id, "key": key})
        except _Stale:
            _mark_stale(package_id)
            raise ProposalError("Der Plan hat sich seit der Berechnung geändert – der Vorschlag ist veraltet und wird "
                                "neu berechnet.") from None
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        p.status, p.decided_at, p.updated_at = "angenommen", utcnow(), utcnow()
        p.decided_by_id, p.decided_by = getattr(user, "id", None), _user_name(user)
        p.decision_note, p.chosen_variant_id = (note or None) and note[:500], variant_id
        p.applied_version = store.version
        for other in db.scalars(select(PlanProposal).where(PlanProposal.status.in_(OPEN_STATES),
                                                           PlanProposal.id != package_id)):
            _close(db, other, "ersetzt", "Ein anderes Paket wurde angenommen")
        for ov in db.scalars(select(PlanProposalVariant).where(PlanProposalVariant.package_id == package_id,
                                                               PlanProposalVariant.id != variant_id)):
            ov.diff = None
        _log(db, package_id, "angenommen", user, variant_id=variant_id, note=note,
             detail={"key": key, "version": store.version, "remaining": info.get("remaining")})
        db.commit()
    informed = _inform(package_id, key, teachers, changes) if key != "vertretung" else []
    if informed:
        with SessionLocal() as db:
            p = db.get(PlanProposal, package_id)
            p.informed = informed
            _log(db, package_id, "informiert", note=f"{len(informed)} Lehrkraft/Lehrkräfte")
            db.commit()
    builder.cancel(None)
    _changed()
    try:
        from .autoplan import planner
        planner.after_decision(accepted=True, key=key)
    except Exception:  # noqa: BLE001
        log.exception("Plan prüfen: Nachprüfung konnte nicht geplant werden")
    return get_package(package_id, with_log=True) or {}


def _mark_stale(package_id: int) -> None:
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        if p is not None and p.status in OPEN_STATES:
            _close(db, p, "veraltet", "Plan seit der Berechnung geändert")
            db.commit()
    _changed()
    try:
        from .autoplan import planner
        planner.after_decision(accepted=False, key="")
    except Exception:  # noqa: BLE001
        pass


def discard(package_id: int, user: Any, reason: str = "") -> dict:
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        if p is None:
            raise ProposalError("Vorschlag nicht gefunden", 404)
        if p.status not in OPEN_STATES:
            raise ProposalError("Dieser Vorschlag ist nicht mehr offen")
        signature = p.signature
        p.decided_at, p.decided_by_id, p.decided_by = utcnow(), getattr(user, "id", None), _user_name(user)
        p.decision_note = (reason or None) and reason[:500]
        _close(db, p, "verworfen", reason, user)
        db.commit()
    builder.cancel(None)
    try:
        from .autoplan import planner
        planner.skip(signature)
    except Exception:  # noqa: BLE001
        pass
    _changed()
    return get_package(package_id, with_log=True) or {}


def postpone(package_id: int, user: Any, hours: int = 24) -> dict:
    hours = max(1, min(int(hours or 24), 24 * 14))
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        if p is None:
            raise ProposalError("Vorschlag nicht gefunden", 404)
        if p.status != "offen":
            raise ProposalError("Dieser Vorschlag ist nicht mehr offen")
        p.postponed_until = utcnow() + timedelta(hours=hours)
        p.postponed_by = _user_name(user)[:80]
        p.updated_at = utcnow()
        _log(db, package_id, "spaeter", user, note=f"{hours} Stunden")
        db.commit()
    _changed()
    return get_package(package_id) or {}


def wake(package_id: int, user: Any) -> dict:
    """Zurückgestellten Vorschlag wieder in die Liste holen."""
    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        if p is None:
            raise ProposalError("Vorschlag nicht gefunden", 404)
        p.postponed_until, p.postponed_by = None, None
        _log(db, package_id, "zurueckgeholt", user)
        db.commit()
    _changed()
    return get_package(package_id) or {}


# =================================================================== Vorschau
def preview_school(package_id: int, variant_id: int):
    """Stundenplan mit angewendeter Variante (Kopie) – für die Entwurfsansicht. ``None``, wenn nicht mehr möglich."""
    from schulmanager import plan_proposals as pp
    from schulmanager.models import School

    with SessionLocal() as db:
        p = db.get(PlanProposal, package_id)
        v = db.get(PlanProposalVariant, variant_id)
        if p is None or v is None or v.package_id != p.id:
            return None
        if v.diff is None:
            return None
        diff = dict(v.diff)
    school = School.from_dict(_store().school.to_dict())
    pp.apply_diff(school, diff)
    return school


# =================================================================== Lehrkräfte informieren
def _inform(package_id: int, key: str, teacher_ids: list[str], changes: list[dict]) -> list[str]:
    """E-Mail (Ausgang) und Live-Ereignis an die betroffenen Lehrkräfte. Liefert die informierten Kürzel."""
    from . import notify
    from .db import session_scope
    from .db_models import User
    from .events import bus

    if not teacher_ids:
        return []
    school = _store().school
    teachers = school.index("teachers")
    informed: list[str] = []
    user_ids: set[int] = set()
    with session_scope() as db:
        users = {u.teacher_id: u for u in db.scalars(select(User).where(User.teacher_id.in_(sorted(teacher_ids)),
                                                                      User.active.is_(True)))}
        for tid in teacher_ids:
            lines = []
            for ch in changes:
                if tid not in ch.get("teachers", []):
                    continue
                label = ch["label"]
                if ch.get("from") or ch.get("to"):
                    lines.append(f"• {label}: {', '.join(ch.get('from') or ['–'])} → {', '.join(ch.get('to') or ['–'])}")
                for rc in ch.get("rooms", []):
                    lines.append(f"• {label}: Raum {', '.join(rc['old']) or '–'} → {', '.join(rc['new']) or '–'} "
                                 f"({rc['where']})")
            u, t = users.get(tid), teachers.get(tid)
            if u is not None:
                user_ids.add(u.id)
            if not lines:
                continue
            informed.append(tid)
            address = (u.email if u and u.email else None) or (getattr(t, "email", "") if t else "")
            if getattr(config, "smtp_enabled", False) and address and "@" in address:
                name = (t.name if t else None) or (u.display_name if u else tid)
                text = "\n".join([f"Guten Tag {name},", "",
                                  "der Stundenplan wurde geändert. Das betrifft Sie:", "", *sorted(set(lines)), "",
                                  f"Aktueller Plan: {config.base_url}/stundenplan", "",
                                  f"Diese Nachricht wurde automatisch erzeugt ({school.settings.school_name})."])
                notify._add(db, "email", address, "Stundenplan geändert: Änderungen für Sie", text,
                            notify._dedupe("plan", str(package_id), address))
    if user_ids:
        try:
            bus.publish("plan_proposal_applied", {"package": package_id, "key": key}, user_ids=user_ids)
        except Exception:  # pragma: no cover
            pass
    try:
        notify.kick()
    except Exception:  # pragma: no cover
        pass
    return informed
