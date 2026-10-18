"""Dauerprüfung des regulären Stundenplans („Plan prüfen“) – schlägt Lösungen vor, entscheidet aber nicht selbst.

Ablauf
------
1. Ein ``change``-Ereignis mit planungsrelevantem Scope (Lehrkräfte, Räume, Klassen, Kurse, Stundentafeln,
   Einstellungen, Stundenplan, Import …) startet nach ``SM_AUTOPLAN_DELAY`` Sekunden Ruhe eine Prüfung
   (mehrere schnelle Änderungen → eine Prüfung; läuft im Hintergrund, blockiert keine Anfrage).
2. :func:`schulmanager.autoplan.prepare_repair` sucht Probleme und bestimmt, was ohne Verschieben geht
   (Raum des richtigen Typs zur selben Zeit, Stunden ohne Kurs entfernen).
3. Gibt es Probleme, legt ``server/proposals.py`` ein **Vorschlagspaket** an: mehrere Varianten (minimal, lokal,
   gründlich, ggf. Vertretung bzw. Räume anpassen), jede mit Kennzahlen vorher/nachher. Die Berechtigten entscheiden
   („Wir nehmen diesen Plan“). Ein neues Paket ersetzt veraltete; verschwindet das Problem, erledigt es sich.
4. **Nichts wird ohne Zustimmung geändert.** Einzige Ausnahme: ``settings.plan_auto_apply = "raeume"`` – reine
   Raumänderungen und das Entfernen verwaister Stunden werden sofort übernommen (Version mit Scope
   ``["timetable", "autoplan"]``, rückgängig über „Verlauf & Audit“).

Abwesenheiten (krank, Klassenfahrt, Raumsperre für einzelne Tage) ändern den regulären Plan nicht – dafür
berechnet die Vertretungs-Engine den Tagesplan bei jeder Änderung sofort neu.

Schutz vor Schleifen: eigene Änderungen (Scope ``autoplan``, ``proposals``) und „Rückgängig“/„Wiederherstellen“
lösen keine Prüfung aus; eine verworfene oder erfolglose Problemlage wird erst nach der nächsten Änderung erneut
versucht. Abschaltbar je Schule (``settings.auto_replan``) und global (``SM_AUTOPLAN=0``).
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from schulmanager.models import School

from .config import config

log = logging.getLogger("schulmanager.autoplan")

TRIGGER_SCOPES = frozenset({"all", "import", "init", "settings", "sites", "subjects", "teachers", "rooms",
                            "classes", "curricula", "courses", "lessons", "timetable"})
IGNORE_SCOPES = frozenset({"autoplan", "undo", "restore"})
JOB_KIND = "proposal"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"


class AutoPlanner:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._timer: Optional[threading.Timer] = None
        self._checking = False
        self._pending = False
        self._enabled = False
        self._skip_signature: Optional[str] = None   # Problemlage ohne weitere Verbesserung → nicht erneut
        self._scopes: set[str] = set()               # Änderungsquellen seit der letzten Prüfung (für das Paket)
        self._force = False                          # „Jetzt prüfen“: vorhandene Pakete neu berechnen
        self.state: dict[str, Any] = {"status": "idle", "message": "Noch keine Prüfung", "checked_at": None,
                                      "applied_at": None, "last": None, "problems": []}

    # ------------------------------------------------------------------ Start/Stopp
    def start(self) -> bool:
        if not config.autoplan:
            log.info("Auto-Planer deaktiviert (SM_AUTOPLAN=0)")
            return False
        from . import proposals
        from .events import bus
        proposals.reset_stale()
        self._skip_signature = None
        self._scopes.clear()
        self._force = False
        bus.add_listener(self._listener)
        self._enabled = True
        self.schedule()          # Stand beim Start einmal prüfen
        log.info("Auto-Planer gestartet")
        return True

    def stop(self) -> None:
        from .events import bus
        bus.remove_listener(self._listener)
        with self._lock:
            self._enabled = False
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------ Auslöser
    def _listener(self, event: str, data: dict) -> None:
        if not self._enabled:
            return
        if event == "change":
            scope = set((data or {}).get("scope") or [])
            if scope & IGNORE_SCOPES:
                if scope & {"undo", "restore"}:
                    # Bewusst zurückgenommen → diesen Stand nicht sofort wieder „reparieren“
                    self.schedule(remember=True)
                return
            if scope & TRIGGER_SCOPES:
                with self._lock:
                    self._scopes |= scope & TRIGGER_SCOPES
                self.schedule()
        elif event == "job" and (data or {}).get("status") in ("done", "failed", "cancelled", "applied"):
            with self._lock:
                if self._pending and (data or {}).get("kind") != "proposal":
                    self._pending = False
                    self.schedule()

    def schedule(self, delay: Optional[float] = None, remember: bool = False) -> None:
        """Prüfung nach ``delay`` Sekunden (Standard ``SM_AUTOPLAN_DELAY``); ein neuer Aufruf startet die Frist neu."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            wait = config.autoplan_delay if delay is None else delay
            self._timer = threading.Timer(max(0.0, wait), self._run, kwargs={"remember": remember})
            self._timer.daemon = True
            self._timer.name = "sm-autoplan"
            self._timer.start()

    def run_now(self) -> dict:
        """Sofort prüfen (Knopf „Jetzt prüfen“) – auch eine schon erfolglos versuchte Problemlage."""
        self._skip_signature = None
        self._force = True
        self._run()
        return self.status()

    # ------------------------------------------------------------------ Prüfung
    def _run(self, remember: bool = False) -> None:
        with self._lock:
            if self._checking:
                self._pending = True
                return
            self._checking = True
        try:
            self._check(remember)
        except Exception as exc:  # noqa: BLE001 - der Auto-Planer darf den Server nie stören
            log.exception("Auto-Planer: Prüfung fehlgeschlagen")
            self._set("error", f"Prüfung fehlgeschlagen: {exc}")
        finally:
            with self._lock:
                self._checking = False
                again = self._pending and not self._job_running()
                if again:
                    self._pending = False
            if again:
                self.schedule()

    def _job_running(self) -> bool:
        from .jobs import manager
        return manager.running() is not None

    def _check(self, remember: bool) -> None:
        from schulmanager import plan_proposals as pp
        from schulmanager.autoplan import prepare_repair
        from . import proposals
        from .routes.features_common import get_store

        store = get_store()
        version, school = store.version, store.school
        plan = prepare_repair(school)
        problems = plan.before.summary(school)
        if not getattr(school.settings, "auto_replan", True):
            self._set("off", "Die Dauerprüfung ist ausgeschaltet", problems=problems)
            return
        if plan.before.empty:
            self._skip_signature = None
            self._force = False
            proposals.close_obsolete()
            self._set("ok", "Stundenplan ist gültig – nichts zu tun", problems=[])
            return
        sig = plan.before.signature()
        if remember:
            self._skip_signature = sig
            self._set("waiting", "Änderung wurde rückgängig gemacht – neue Vorschläge erst nach der "
                                 "nächsten Änderung", problems=problems)
            return
        state = pp.state_hash(school, plan.before)
        if self._force:
            self._force = False
            proposals.supersede_others(None)
        elif proposals.is_covered(sig):
            proposals.supersede_others(state)
            self._set("covered", "Die Probleme werden laut Entscheidung per Vertretung abgedeckt", problems=problems)
            return
        existing = proposals.find_for_state(state)
        if existing is not None:
            if existing.status == "offen":
                self._set("proposal", "Lösungsvorschläge liegen zur Entscheidung vor", problems=problems)
            else:
                self._set("running", "Lösungsvorschläge werden berechnet …", problems=problems)
            return
        proposals.supersede_others(state)
        if sig == self._skip_signature:
            self._set("unsolved", "Keine Vorschläge: verworfen oder keine bessere Lösung gefunden – die nächste "
                                  "Änderung löst eine neue Prüfung aus", problems=problems)
            return
        if not plan.free_courses and getattr(school.settings, "plan_auto_apply", "aus") == "raeume":
            self._apply_direct(version, plan, problems)
            return
        if plan.free_courses and self._job_running():
            with self._lock:
                self._pending = True
            self._set("waiting", "Wartet, bis der laufende Generator fertig ist", problems=problems)
            return
        with self._lock:
            scopes = sorted(self._scopes)
            self._scopes.clear()
        self._set("running", "Lösungsvorschläge werden berechnet …", problems=problems)
        proposals.start_package(School.from_dict(school.to_dict()), plan, version, problems, scopes)

    # ------------------------------------------------------------------ Rückmeldungen der Vorschläge
    def proposal_ready(self, package_id: int, ok: bool) -> None:
        """Vom Vorschlags-Builder aufgerufen, wenn ein Paket fertig berechnet ist."""
        if ok:
            self._set("proposal", "Lösungsvorschläge liegen zur Entscheidung vor", problems=None)
        else:
            self._skip_signature = self._current_signature()
            self._set("unsolved", "Keine bessere Lösung gefunden – bitte von Hand nachbessern", problems=None)
        try:
            from .events import bus
            bus.publish("autoplan", {"status": self.state["status"], "message": self.state["message"]},
                        permission="timetable.generate")
        except Exception:  # pragma: no cover
            pass

    def _current_signature(self) -> Optional[str]:
        try:
            from schulmanager.autoplan import find_problems
            from .routes.features_common import get_store
            return find_problems(get_store().school).signature()
        except Exception:  # noqa: BLE001
            return None

    def after_decision(self, accepted: bool, key: str) -> None:
        """Nach „Annehmen“ (Rest prüfen) bzw. veraltetem Paket (neu berechnen)."""
        if self._enabled:
            self._skip_signature = None
            self.schedule(1.0)

    def skip(self, signature: Optional[str]) -> None:
        """Verworfene Problemlage nicht sofort wieder vorschlagen."""
        self._skip_signature = signature
        self._set("unsolved", "Vorschlag verworfen – die nächste Änderung löst eine neue Prüfung aus")


    # ------------------------------------------------------------------ nur Räume / verwaiste Stunden
    def _apply_direct(self, version: int, plan, problems: list[str]) -> None:
        """Nur mit ``settings.plan_auto_apply = "raeume"``: reine Raumänderungen sofort übernehmen."""
        from . import proposals
        lessons = [le.to_dict() for le in plan.school.lessons]
        n_rooms, n_orphans = len(plan.room_changes), len(plan.removed_orphans)
        parts = []
        if n_rooms:
            parts.append(f"{n_rooms} Raumwechsel")
        if n_orphans:
            parts.append(f"{n_orphans} Stunde(n) ohne Kurs entfernt")
        text = "Automatische Neuplanung: " + ", ".join(parts)
        if problems:
            text += " – Anlass: " + "; ".join(problems[:3])
        info = self._commit(version, lessons, text, problems, before_count=plan.before.count(),
                            signature=plan.before.signature())
        if not isinstance(info, dict):
            return
        last = {"kind": "rooms", "room_changes": plan.room_changes[:100], "removed": n_orphans,
                "changes": [], "reasons": problems, "at": _now()}
        self._finish_applied(info, last)
        proposals.supersede_others(None)


    # ------------------------------------------------------------------ Übernehmen
    def _commit(self, base_version: int, lessons_data: list[dict], message: str, problems: list[str], *,
                before_count: int, signature: Optional[str] = None, final: bool = True) -> dict | str:
        """Ersetzt den Stundenplan, wenn er dadurch besser wird. Sonst ``"changed"`` (Plan inzwischen geändert →
        neu prüfen) bzw. ``"worse"`` (keine Verbesserung; ``final=False``: Aufrufer versucht es weiter)."""
        from schulmanager.autoplan import find_problems
        from schulmanager.models import Lesson
        from schulmanager.timetable import validate_school
        from .routes.features_common import get_store, mutate

        info: dict = {}
        store = get_store()

        class _Skip(Exception):
            pass

        def fn(school):
            if store.version != base_version:
                raise _Skip("changed")
            courses = school.index("courses")
            before_conf = validate_school(school)["stats"]["conflicts"]
            old_ids = {le.id for le in school.lessons}
            new = []
            for d in lessons_data:
                le = Lesson.from_dict(d)
                c = courses.get(le.course_id)
                if c is None:
                    continue
                n = len(c.parts)
                le.rooms = (list(le.rooms) + [None] * n)[:n]
                new.append(le)
            school.lessons = new
            after = find_problems(school)
            after_conf = validate_school(school)["stats"]["conflicts"]
            if after.count() >= before_count or after_conf > before_conf:
                info["after"] = after
                raise _Skip("no improvement")
            gone = old_ids - {le.id for le in new}      # Tagesentscheidungen zu verlegten Stunden gelten nicht mehr
            school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
            info.update(after=after, remaining=after.summary(school), fixed=before_count - after.count())
            return info

        try:
            mutate(None, message[:480], fn, scope=["timetable", "autoplan"])
        except _Skip as exc:
            if str(exc) == "changed":
                self.schedule(0.5)
                return "changed"
            if final:
                self._skip_signature = signature
                self._set("unsolved", "Keine bessere Lösung gefunden – bitte von Hand nachbessern",
                          problems=problems)
            return "worse"
        after = info.get("after")
        # Rest, den auch dieser Lauf nicht lösen konnte, nicht endlos neu versuchen
        self._skip_signature = after.signature() if after is not None and not after.empty else None
        return info

    def _finish_applied(self, info: dict, last: dict) -> None:
        remaining = info.get("remaining") or []
        last["fixed"] = info.get("fixed", 0)
        last["remaining"] = remaining
        msg = f"{info.get('fixed', 0)} Problem(e) automatisch behoben"
        if remaining:
            msg += f", {len(remaining)} offen"
        with self._lock:
            self.state["applied_at"] = last["at"]
            self.state["last"] = last
        self._set("applied" if not remaining else "partial", msg, problems=remaining)
        try:
            from .events import bus
            bus.publish("autoplan", {"status": self.state["status"], "message": msg},
                        permission="timetable.generate")
        except Exception:  # pragma: no cover
            pass
        log.info("Auto-Planer: %s", msg)

    # ------------------------------------------------------------------ Status
    def _set(self, status: str, message: str, problems: Optional[list[str]] = None, job_id: Optional[str] = None
             ) -> None:
        with self._lock:
            self.state.update(status=status, message=message, checked_at=_now(), job_id=job_id)
            if problems is not None:
                self.state["problems"] = list(problems)

    def status(self) -> dict:
        with self._lock:
            out = dict(self.state)
        out["enabled"] = self._enabled
        out["checking"] = self._checking
        return out


planner = AutoPlanner()


def start() -> bool:
    return planner.start()


def stop() -> None:
    planner.stop()
