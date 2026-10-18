"""Hintergrund-Jobs: Stundenplan-Generierung in einem eigenen Prozess.

Der Generator (``scheduler.generate``) ist reines, CPU-lastiges Python. Damit der
Webserver reaktionsfähig bleibt, läuft er in einem separaten Prozess
(``multiprocessing``-Kontext „spawn“). Die Schule wird als Dict übergeben,
Fortschritt und Ergebnis kommen über eine Queue zurück. Das Ergebnis wird als
**Entwurf** gehalten (``stats``, ``unplaced``, ``warnings``, ``lessons``) und erst mit
:func:`apply` per ``store.mutate(..., scope=["timetable"])`` übernommen.

Es läuft immer höchstens ein Job gleichzeitig; Jobs können abgebrochen werden.
Zustandsänderungen werden als Event ``job`` über ``bus.publish`` verteilt.

**Neuplanung für eine Lehrkraft** (``kind="replan_teacher"``, Lehrer-Selbstverwaltung §9.3): Alle Stunden
außer denen der Lehrkraft (Kurse, in denen sie einen Teil unterrichtet; optional alle Kurse ihrer Klassen)
werden für den Generator fixiert. Das Ergebnis wird mit dem Ausgangsplan zusammengeführt: unveränderte Stunden
behalten ID, Raum und Fixierung, nur neu gelegte Stunden bekommen neue IDs und freie Räume. „Übernehmen“
ersetzt ausschließlich die Stunden der geänderten Kurse (409, wenn diese inzwischen anderweitig geändert wurden
oder dadurch neue Konflikte entstünden).

**Plan prüfen** (``kind="proposal"``, ``server/proposals.py``): wie die Neuplanung einer Lehrkraft, aber frei sind die
vom Problem betroffenen Kurse (je nach Variante mehr); das zusammengeführte Ergebnis wird nicht übernommen, sondern
als Variante eines Vorschlagspakets gespeichert (Entscheidung durch die Planung).

Dieses Modul importiert auf oberster Ebene nur Standardbibliothek + Kernmodelle,
damit der Kindprozess schnell startet.
"""
from __future__ import annotations

import logging
import multiprocessing as mp
import queue as queue_mod
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

log = logging.getLogger("schulmanager.jobs")

RUNNING_STATES = ("queued", "running")
FINAL_STATES = ("done", "failed", "cancelled", "applied")
MAX_JOBS_KEPT = 10
MAX_VARIANTS = 5
VARIANT_SEED_STEP = 1000      # Variante i rechnet mit Startwert + i * 1000 (parallele Läufe: + 0, 1, 2 …)


class JobError(RuntimeError):
    """Fehler beim Starten/Übernehmen eines Jobs (``status`` = HTTP-Status)."""

    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- Kindprozess
def _worker(school_dict: dict, params: dict, q) -> None:  # pragma: no cover - läuft im Kindprozess
    """Einstiegspunkt des Generator-Prozesses."""
    try:
        import os
        import signal

        def _terminate(signum, frame):
            # Hilfsprozesse von generate_best_of mit beenden
            for child in mp.active_children():
                child.terminate()
            os._exit(143)

        signal.signal(signal.SIGTERM, _terminate)

        from schulmanager.models import School
        from schulmanager import scheduler

        school = School.from_dict(school_dict)
        last = [0.0]

        def progress(msg: str, fraction: float) -> None:
            now = time.monotonic()
            if now - last[0] >= 0.2 or fraction >= 1.0:
                last[0] = now
                q.put(("progress", str(msg), float(fraction)))

        q.put(("progress", "Start", 0.0))
        workers = int(params.get("workers", 1) or 0)
        n_var = max(1, min(MAX_VARIANTS, int(params.get("variants", 1) or 1)))

        def run(seed: int, prog) -> Any:
            kw = dict(time_limit=float(params.get("time_limit", 30.0)), seed=seed,
                      keep_locked=bool(params.get("keep_locked", True)), progress=prog)
            return scheduler.generate_best_of(school, workers=workers, **kw)     # workers=1: ein Lauf

        if not params.get("evaluate"):      # Neuplanung/Plan-Prüfung: nur der Plan, ohne Auswertung
            res = run(int(params.get("seed", 1)), progress)
            q.put(("result", {
                "lessons": [le.to_dict() for le in res.lessons],
                "unplaced": list(res.unplaced),
                "stats": dict(res.stats),
                "warnings": list(res.warnings),
            }))
            return

        from schulmanager import generator_report as gr
        before = School.from_dict(school_dict)
        cost_before, parts_before = gr.plan_cost_info(before)
        variants: list[dict] = []
        for i in range(n_var):
            seed_i = int(params.get("seed", 1)) + i * VARIANT_SEED_STEP

            def prog_i(msg: str, fraction: float, _i: int = i) -> None:
                label = f"Variante {_i + 1} von {n_var}: {msg}" if n_var > 1 else msg
                progress(label, (_i + max(0.0, min(0.95, fraction))) / n_var)

            res = run(seed_i, prog_i)
            after = School.from_dict(school_dict)
            if params.get("period"):        # Planzeitraum: wie später beim Übernehmen stempeln (plan_periods.finalize)
                from schulmanager import plan_periods as pp
                pp.finalize(after, res.lessons, params["period"])
            after.lessons = list(res.lessons)
            progress(f"Variante {i + 1} von {n_var}: Auswertung" if n_var > 1 else "Auswertung", (i + 0.97) / n_var)
            ev = gr.evaluate(before, after, warnings=list(res.warnings), cost_before=cost_before,
                             parts_before=parts_before)
            stats = dict(res.stats)
            stats["seed"] = seed_i
            variants.append({"index": i, "seed": seed_i, "lessons": [le.to_dict() for le in res.lessons],
                             "unplaced": list(res.unplaced), "stats": stats, "warnings": list(res.warnings),
                             "trace": list(res.trace), "runs": list(res.runs), "evaluation": ev})
        best = min(range(len(variants)), key=lambda k: gr.rank_key(variants[k]["evaluation"]))
        top = variants[best]
        q.put(("result", {
            "lessons": top["lessons"], "unplaced": top["unplaced"], "stats": top["stats"], "warnings": top["warnings"],
            "variants": variants, "best_variant": best, "cost_before": cost_before,
        }))
    except BaseException as exc:  # noqa: BLE001 - alles an den Elternprozess melden
        q.put(("error", f"{type(exc).__name__}: {exc}", traceback.format_exc(limit=8)))


# ---------------------------------------------------------------- Neuplanung einer Lehrkraft
REPLAN_SCOPES = ("teacher", "classes")
PIN_SEP = "@fix:"   # Kennung der Hilfskurse für fixierte fremde Stunden (nur in der Generator-Eingabe)


def _pin_foreign_lessons(work, free: set[str]) -> int:
    """Fixiert fremde Stunden in der Generator-Eingabe **samt Räumen**.

    Der Generator verteilt die Räume fixierter Stunden beim Vorbelegen neu (der Reihe nach, erster freier Raum
    des Typs). Dabei kann eine fremde Stunde in einen Raum am anderen Standort geraten und dann an der Wegezeit
    scheitern („kollidiert und wurde verworfen“) – fremde Stunden würden verschoben. Deshalb wird jede Stunde
    eines nicht freien Kurses zu einem eigenen Hilfskurs ``<kurs>@fix:<stunde>`` mit genau dieser einen Stunde
    und ihren bisherigen Räumen als festen Räumen. Die Originalkurse fehlen in der Eingabe, also plant der
    Generator dort auch keine bisher unverplanten Stunden nach. Liefert die Anzahl fixierter Stunden.
    """
    from schulmanager.models import Course, CoursePart

    courses = work.index("courses")
    pinned: list = []
    count = 0
    for le in work.lessons:
        if le.course_id in free:
            continue
        c = courses.get(le.course_id)
        if c is None:
            continue
        parts = []
        for i, p in enumerate(c.parts):
            room = le.rooms[i] if i < len(le.rooms) and le.rooms[i] else p.room
            parts.append(CoursePart(subject=p.subject, teacher=p.teacher, room=room, room_type=p.room_type,
                                    label=p.label))
        pid = f"{c.id}{PIN_SEP}{le.id}"
        pinned.append(Course(pid, list(c.classes), parts, le.length, False, c.label, list(le.weeks), c.origin,
                             rhythm=le.rhythm))
        le.course_id, le.locked = pid, True
        count += 1
    work.courses = [c for c in work.courses if c.id in free] + pinned
    return count


def _lesson_key(le, _ctx=None) -> tuple:
    """Identität eines Blocks: (Tag, Beginn, Länge, Wochen). Die Wochen sind die laufenden Wochen 1 … 53, in denen
    die Wochenangabe der Stunde gilt (leer = jede Woche)."""
    from schulmanager.models import lesson_in_range, spec_active
    if le.weeks or le.rhythm or le.from_week or le.to_week:     # Planzeitraum (from/to) begrenzt die Wochen ebenfalls
        weeks = tuple(w for w in range(1, 54) if spec_active(le.weeks, le.rhythm, w) and lesson_in_range(le, w))
    else:
        weeks = ()
    return (le.day, le.start, le.length, weeks)


def _by_course(lessons) -> dict[str, list]:
    out: dict[str, list] = {}
    for le in lessons:
        out.setdefault(le.course_id, []).append(le)
    return out


def replan_courses(school, teacher_id: str, scope: str = "teacher") -> list[str]:
    """Kurse, die bei der Neuplanung frei bleiben: Kurse der Lehrkraft (``scope="classes"``: zusätzlich alle
    Kurse ihrer Klassen – mehr Spielraum, verschiebt aber auch Stunden anderer Lehrkräfte dieser Klassen)."""
    own = [c for c in school.courses if any(p.teacher == teacher_id for p in c.parts)]
    if scope == "classes":
        classes = {cid for c in own for cid in c.classes}
        return sorted(c.id for c in school.courses if set(c.classes) & classes)
    return sorted(c.id for c in own)


def prepare_replan(school, teacher_id: str, scope: str = "teacher") -> tuple[dict, dict]:
    """Generator-Eingabe für die Neuplanung: alle Stunden außer denen der freien Kurse werden fixiert – samt
    ihren Räumen (siehe :func:`_pin_foreign_lessons`).

    Fixierungen der Planung in den freien Kursen bleiben erhalten (der Generator verwirft sie, wenn sie nach
    den neuen Sperrzeiten nicht mehr gültig sind). Liefert ``(school_dict, context)``. ValueError, wenn die
    Lehrkraft keinen Unterricht hat.
    """
    from schulmanager.models import School

    if scope not in REPLAN_SCOPES:
        raise ValueError(f"Unbekannter Umfang „{scope}“")
    if teacher_id not in school.index("teachers"):
        raise ValueError(f"Lehrkraft {teacher_id} existiert nicht")
    free = replan_courses(school, teacher_id, scope)
    if not free:
        raise ValueError("Die Lehrkraft hat keinen Unterricht – es gibt nichts neu zu planen")
    work = School.from_dict(school.to_dict())
    pinned = _pin_foreign_lessons(work, set(free))
    context = {"teacher_id": teacher_id, "scope": scope, "free_courses": free, "school": school.to_dict(),
               "pinned": pinned}
    return work.to_dict(), context


def merge_replan(base_dict: dict, result_lessons: list[dict], free_courses: list[str], strict: bool = True) -> dict:
    """Führt das Generator-Ergebnis mit dem Ausgangsplan zusammen (siehe Moduldoku).

    Übernommen werden nur Stunden der freien Kurse; alle übrigen Stunden kommen unverändert aus dem Ausgangsplan
    (Hilfskurse ``…@fix:…`` des Generators werden ignoriert). Neu gelegte Stunden, die dort trotzdem kollidieren
    würden, entfallen (``dropped``, als unverplant gemeldet) – so entsteht nie ein neuer Konflikt.

    ``strict=False`` (Auto-Planer): keine Einzelprüfung per ``move_lesson`` – die ist strenger als der Generator
    (z. B. „Fach höchstens N× am Tag“, das der Generator bei Sperrtagen bewusst lockert); Räume kommen aus dem
    Generator-Ergebnis. Harte Regeln prüft der Auto-Planer danach selbst (``autoplan.find_problems``).

    Liefert ``{"lessons", "changed_courses", "base_keys", "changes", "moved", "warnings", "dropped"}``.
    """
    from schulmanager.models import Lesson, School
    from schulmanager.timetable import move_lesson

    base = School.from_dict(base_dict)
    n_weeks = (base, base.index("courses"))
    free_set = set(free_courses)
    res = [le for le in (Lesson.from_dict(d) for d in result_lessons) if le.course_id in free_set]
    base_by, res_by = _by_course(base.lessons), _by_course(res)
    changed = set(free_set)
    nums = [int(le.id[1:]) for le in base.lessons if le.id[:1] == "L" and le.id[1:].isdigit()]
    counter = [max(nums, default=0)]
    taken = {le.id for le in base.lessons}

    def new_id() -> str:
        while True:
            counter[0] += 1
            lid = f"L{counter[0]}"
            if lid not in taken:
                taken.add(lid)
                return lid

    merged = [le for le in base.lessons if le.course_id not in changed]
    fresh: list = []
    for cid in sorted(changed):
        olds = list(base_by.get(cid, []))
        for le in res_by.get(cid, []):
            match = next((o for o in olds if _lesson_key(o, n_weeks) == _lesson_key(le, n_weeks)), None)
            if match is not None:
                olds.remove(match)
                le.id, le.locked = match.id, match.locked
                if strict:
                    le.rooms = list(match.rooms)
            else:
                le.id, le.locked = new_id(), False
                fresh.append(le)
            merged.append(le)
    base.lessons = merged
    warnings: list[str] = []
    dropped: list[dict] = []
    for le in (fresh if strict else []):  # gegen den zusammengeführten Plan prüfen (ggf. freien Raum wählen)
        try:
            move_lesson(base, le.id, le.day, le.start)
        except (ValueError, KeyError) as exc:
            conf = exc.args[0] if exc.args and isinstance(exc.args[0], list) else [str(exc)]
            base.lessons = [x for x in base.lessons if x.id != le.id]
            dropped.append({"course": le.course_id, "length": le.length, "weeks": list(le.weeks), "rhythm": le.rhythm,
                            "reason": "; ".join(conf[:3])})
            warnings.append(f"Stunde {le.course_id} ({le.day + 1}. Tag, {le.start + 1}. Std.) hätte kollidiert "
                            "und bleibt unverplant: " + "; ".join(conf[:3]))
    kept = {x.id for x in base.lessons}
    fresh = [le for le in fresh if le.id in kept]
    merged = base.lessons
    after_by = _by_course([x for x in merged if x.course_id in changed])
    courses = base.index("courses")
    days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    def where(le) -> str:
        from schulmanager.weeks import describe
        span = f"{le.start + 1}." + (f"–{le.start + le.length}." if le.length > 1 else "")
        weeks = _lesson_key(le, n_weeks)[3]
        wl = f" ({describe(weeks)})" if weeks else ""
        return f"{days[le.day] if le.day < len(days) else le.day} {span}{wl}"

    changes = []
    for cid in sorted(changed):
        before = sorted((x for x in base_by.get(cid, [])), key=lambda x: _lesson_key(x, n_weeks))
        after_keys = {_lesson_key(x, n_weeks) for x in after_by.get(cid, [])}
        before_keys = {_lesson_key(x, n_weeks) for x in before}
        removed = [where(x) for x in before if _lesson_key(x, n_weeks) not in after_keys]
        added = [where(x) for x in sorted(after_by.get(cid, []), key=lambda x: _lesson_key(x, n_weeks))
                 if _lesson_key(x, n_weeks) not in before_keys]
        if removed or added:
            c = courses.get(cid)
            changes.append({"course_id": cid, "label": (c.label or cid) if c else cid,
                            "classes": list(c.classes) if c else [], "from": removed, "to": added})
    base_keys = {cid: [list(k[:3]) + [list(k[3])] for k in sorted(_lesson_key(x, n_weeks)
                                                                     for x in base_by.get(cid, []))]
                 for cid in changed}
    return {"lessons": [le.to_dict() for le in merged], "changed_courses": sorted(changed), "base_keys": base_keys,
            "changes": changes[:200], "moved": len(fresh), "warnings": warnings, "dropped": dropped}


# ---------------------------------------------------------------- Job-Verwaltung
def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"


@dataclass
class Job:
    id: str
    kind: str
    params: dict
    user_id: Any = None
    user_name: str = ""
    base_version: Any = None
    status: str = "queued"           # queued|running|done|failed|cancelled|applied
    progress: float = 0.0
    message: str = "Wartet"
    created_at: str = field(default_factory=_now)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    applied_at: Optional[str] = None
    applied_version: Any = None
    error: Optional[str] = None
    result: Optional[dict] = None
    process: Any = None
    queue: Any = None
    context: dict = field(default_factory=dict)   # interne Daten (z. B. Ausgangsplan der Neuplanung)

    def public(self, with_lessons: bool = False) -> dict:
        out = {
            "id": self.id, "kind": self.kind, "status": self.status,
            "progress": round(self.progress, 3), "message": self.message,
            "params": self.params, "user": self.user_name, "base_version": self.base_version,
            "created_at": self.created_at, "started_at": self.started_at,
            "finished_at": self.finished_at, "applied_at": self.applied_at,
            "applied_version": self.applied_version, "error": self.error,
        }
        if self.result is not None:
            out["stats"] = self.result.get("stats", {})
            out["unplaced"] = self.result.get("unplaced", [])
            out["warnings"] = self.result.get("warnings", [])
            out["lessons_count"] = len(self.result.get("lessons", []))
            if "replan" in self.result:
                out["replan"] = self.result["replan"]
                out["changes"] = self.result.get("changes", [])
            if with_lessons:
                out["lessons"] = self.result.get("lessons", [])
            if self.result.get("variants"):
                out["best_variant"] = self.result.get("best_variant", 0)
                out["applied_variant"] = self.context.get("applied_variant")
                out["variants"] = [variant_summary(v) for v in self.result["variants"]]
        return out

    def event(self) -> dict:
        return {"id": self.id, "kind": self.kind, "status": self.status,
                "progress": round(self.progress, 3), "message": self.message}


def variant_summary(v: dict) -> dict:
    """Kurzfassung einer Variante für die Vergleichstabelle (ohne Stunden, Verlauf und Einzellisten)."""
    ev = v.get("evaluation") or {}
    moves = (ev.get("moves") or {}).get("counts") or {}
    return {"index": v["index"], "seed": v["seed"], "stats": v.get("stats", {}),
            "unplaced_count": len(v.get("unplaced", [])), "lessons_count": len(v.get("lessons", [])),
            "kpis": ev.get("kpis", []), "moved": moves.get("moved", 0) + moves.get("added", 0) + moves.get("removed", 0)}


class JobManager:
    """Verwaltet Generator-Jobs (prozesslokal, ein laufender Job gleichzeitig)."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._ctx = mp.get_context("spawn")

    # ------------------------------------------------------------ Abfragen
    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def running(self) -> Optional[Job]:
        with self._lock:
            for j in self._jobs.values():
                if j.status in RUNNING_STATES:
                    return j
        return None

    # ------------------------------------------------------------ Start
    def start_generate(self, school_dict: dict, params: dict, user=None, base_version=None,
                       kind: str = "generate", context: Optional[dict] = None) -> Job:
        with self._lock:
            if self.running() is not None:
                raise JobError("Es läuft bereits eine Stundenplan-Generierung", 409)
            job = Job(id=uuid.uuid4().hex[:12], kind=kind, params=dict(params),
                      user_id=getattr(user, "id", None),
                      user_name=getattr(user, "display_name", None) or getattr(user, "username", "") or "",
                      base_version=base_version, context=dict(context or {}))
            self._jobs[job.id] = job
            self._prune()
            q = self._ctx.Queue()
            proc = self._ctx.Process(target=_worker, args=(school_dict, job.params, q),
                                     name=f"sm-generate-{job.id}", daemon=False)
            job.queue, job.process = q, proc
            try:
                proc.start()
            except Exception as exc:  # pragma: no cover - z. B. keine Prozesse erlaubt
                job.status, job.error, job.message = "failed", str(exc), "Start fehlgeschlagen"
                job.finished_at = _now()
                self._emit(job)
                raise JobError(f"Generator konnte nicht gestartet werden: {exc}", 500) from exc
            job.status, job.message, job.started_at = "running", "Gestartet", _now()
        self._emit(job)
        threading.Thread(target=self._watch, args=(job,), name=f"sm-job-watch-{job.id}", daemon=True).start()
        return job

    def _prune(self) -> None:
        done = [j for j in self.list() if j.status in FINAL_STATES]
        for j in done[MAX_JOBS_KEPT:]:
            self._jobs.pop(j.id, None)

    # ------------------------------------------------------------ Überwachung
    def _watch(self, job: Job) -> None:
        q, proc = job.queue, job.process
        last_emit = 0.0
        while True:
            try:
                msg = q.get(timeout=0.25)
            except queue_mod.Empty:
                if job.status == "cancelled":
                    break
                if not proc.is_alive():
                    # Prozess beendet – evtl. liegen noch Nachrichten in der Queue
                    try:
                        msg = q.get(timeout=1.0)
                    except queue_mod.Empty:
                        with self._lock:
                            if job.status == "running":
                                job.status = "failed"
                                job.error = f"Generator-Prozess unerwartet beendet (Code {proc.exitcode})"
                                job.message = "Fehlgeschlagen"
                                job.finished_at = _now()
                        self._emit(job)
                        break
                else:
                    continue
            kind = msg[0]
            if job.status == "cancelled":
                break
            if kind == "progress":
                job.message, job.progress = msg[1], max(0.0, min(1.0, msg[2]))
                now = time.monotonic()
                if now - last_emit >= 0.5:
                    last_emit = now
                    self._emit(job)
            elif kind == "result":
                result = msg[1]
                if job.kind in ("replan_teacher", "proposal") and job.status == "running":
                    try:
                        result = self._finish_replan(job, result)
                    except Exception as exc:  # noqa: BLE001 - als fehlgeschlagener Job melden
                        log.exception("Neuplanung %s: Zusammenführen fehlgeschlagen", job.id)
                        with self._lock:
                            if job.status == "running":
                                job.status, job.error, job.message = "failed", str(exc), "Fehlgeschlagen"
                                job.finished_at = _now()
                        self._emit(job)
                        self._autoplan_done(job)
                        break
                with self._lock:
                    if job.status == "running":
                        job.result = result
                        job.status, job.progress, job.finished_at = "done", 1.0, _now()
                        n = len(job.result.get("unplaced", []))
                        job.message = "Fertig" + (f" ({n} Blöcke nicht verplant)" if n else "")
                self._emit(job)
                self._autoplan_done(job)
                break
            elif kind == "error":
                with self._lock:
                    if job.status == "running":
                        job.status, job.error, job.message = "failed", msg[1], "Fehlgeschlagen"
                        job.finished_at = _now()
                log.error("Generator-Job %s fehlgeschlagen: %s\n%s", job.id, msg[1], msg[2] if len(msg) > 2 else "")
                self._emit(job)
                self._autoplan_done(job)
                break
        self._cleanup(job)

    @staticmethod
    def _autoplan_done(job: Job) -> None:
        """Ergebnis eines Vorschlags-Jobs an den Builder geben (``server/proposals.py``)."""
        if job.kind != "proposal":
            return
        try:
            from schulmanager.server.proposals import builder
            builder.job_finished(job)
        except Exception:  # noqa: BLE001
            log.exception("Vorschlags-Job %s: Auswertung fehlgeschlagen", job.id)

    def _cleanup(self, job: Job) -> None:
        proc = job.process
        if proc is not None:
            proc.join(timeout=2)
            if proc.is_alive():  # pragma: no cover
                proc.kill()
                proc.join(timeout=2)
        try:
            if job.queue is not None:
                job.queue.close()
                job.queue.join_thread()
        except Exception:  # pragma: no cover
            pass
        job.process = job.queue = None

    # ------------------------------------------------------------ Abbruch
    def cancel(self, job_id: str) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobError("Job nicht gefunden", 404)
            if job.status not in RUNNING_STATES:
                raise JobError("Job läuft nicht mehr", 409)
            job.status, job.message, job.finished_at = "cancelled", "Abgebrochen", _now()
            proc = job.process
        if proc is not None and proc.is_alive():
            proc.terminate()
        self._emit(job)
        self._autoplan_done(job)
        return job

    # ------------------------------------------------------------ Neuplanung: Ergebnis zusammenführen
    def _finish_replan(self, job: Job, result: dict) -> dict:
        base = job.context.pop("school", None)
        if base is None:
            raise RuntimeError("Ausgangsplan der Neuplanung fehlt")
        merged = merge_replan(base, result.get("lessons", []), job.context.get("free_courses", []),
                              strict=job.kind != "proposal")
        job.context["changed_courses"] = merged["changed_courses"]
        job.context["base_keys"] = merged["base_keys"]
        free = set(job.context.get("free_courses", []))
        unplaced = [u for u in result.get("unplaced", []) if u.get("course") in free] + merged["dropped"]
        out = dict(result)
        out["lessons"] = merged["lessons"]
        out["unplaced"] = unplaced
        # Hinweise des Generators zu Hilfskursen fixierter fremder Stunden sind für die Planung ohne Belang
        out["warnings"] = [w for w in result.get("warnings", []) if PIN_SEP not in w] + merged["warnings"]
        out["stats"] = {**dict(result.get("stats", {})), "unplaced": len(unplaced), "moved": merged["moved"],
                        "changed_courses": len(merged["changes"])}
        out["replan"] = {"teacher_id": job.context.get("teacher_id"), "scope": job.context.get("scope"),
                         "free_courses": len(free), "changed_courses": merged["changed_courses"],
                         "moved": merged["moved"]}
        out["changes"] = merged["changes"]
        return out

    def _apply_replan(self, job: Job, lessons_data: list[dict], user) -> dict:
        """Übernahme einer Neuplanung: ersetzt nur die Stunden der geänderten Kurse."""
        from schulmanager.models import Lesson
        from schulmanager.server.routes.features_common import mutate
        from schulmanager.timetable import validate_school

        changed = set(job.context.get("changed_courses", []))
        base_keys = job.context.get("base_keys", {})
        teacher_id = job.context.get("teacher_id") or job.params.get("teacher_id")
        info: dict = {}

        def fn(school):
            n_weeks = (school, school.index("courses"))
            current = _by_course(school.lessons)
            for cid in changed:
                now = [list(k[:3]) + [list(k[3])] for k in sorted(_lesson_key(x, n_weeks)
                                                                  for x in current.get(cid, []))]
                if now != base_keys.get(cid, []):
                    raise JobError("Der Stundenplan dieser Kurse wurde inzwischen geändert – bitte erneut neu planen",
                                   409)
            before = validate_school(school)["stats"]["conflicts"]
            keep = [le for le in school.lessons if le.course_id not in changed]
            ids = {le.id for le in keep}
            courses = school.index("courses")
            new = []
            for d in lessons_data:
                if d.get("course_id") not in changed or d.get("course_id") not in courses:
                    continue
                le = Lesson.from_dict(d)
                if le.id in ids:
                    raise JobError("Lesson-ID-Konflikt beim Zusammenführen – bitte erneut neu planen", 409)
                n = len(courses[le.course_id].parts)
                le.rooms = (list(le.rooms) + [None] * n)[:n]
                new.append(le)
            removed = {le.id for le in school.lessons if le.course_id in changed}
            school.lessons = keep + new
            after = validate_school(school)["stats"]["conflicts"]
            if after > before:
                raise JobError(f"Übernahme würde {after - before} neue Konflikte erzeugen – bitte erneut neu planen",
                               409)
            gone = removed - {le.id for le in new}   # Entscheidungen zu verlegten Stunden gelten nicht mehr
            school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
            info.update(lessons=len(new), courses=len(changed))
            return info

        mutate(user, f"Stundenplan für Lehrkraft {teacher_id} neu geplant ({len(changed)} Kurse)", fn,
               scope=["timetable"])
        return info

    # ------------------------------------------------------------ Übernahme
    def variant_of(self, job_id: str, index: Optional[int]) -> dict:
        """Eine Variante des fertigen Jobs (``index=None``: die beste). ``JobError`` 404/409 sonst."""
        job = self._jobs.get(job_id)
        if job is None:
            raise JobError("Job nicht gefunden", 404)
        if job.result is None or job.status not in ("done", "applied", "applying"):
            raise JobError("Der Job ist noch nicht fertig", 409)
        variants = job.result.get("variants") or []
        if not variants:
            raise JobError("Dieser Lauf hat keine Varianten", 404)
        i = job.result.get("best_variant", 0) if index is None else index
        if not 0 <= i < len(variants):
            raise JobError("Variante nicht gefunden", 404)
        return variants[i]

    def apply(self, job_id: str, user, variant: Optional[int] = None, regenerate_duties: bool = False) -> dict:
        """Übernimmt den Entwurf (bzw. die gewählte Variante) in den Stundenplan (``store.mutate``, Scope ``timetable``)."""
        from schulmanager.models import Lesson
        from schulmanager.server.routes.features_common import mutate

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobError("Job nicht gefunden", 404)
            if job.status == "applied":
                raise JobError("Dieser Entwurf wurde bereits übernommen", 409)
            if job.kind == "proposal":
                raise JobError("Ergebnisse der Plan-Prüfung werden über die Vorschläge entschieden", 409)
            if job.status != "done" or job.result is None:
                raise JobError("Der Job ist noch nicht fertig", 409)
            lessons_data = list(job.result.get("lessons", []))
            if variant is not None:
                lessons_data = list(self.variant_of(job_id, variant)["lessons"])
                job.context["applied_variant"] = variant
            job.status = "applying"

        info: dict = {}

        if job.kind == "replan_teacher":
            try:
                info = self._apply_replan(job, lessons_data, user)
            except Exception:
                with self._lock:
                    job.status = "done"
                raise
            with self._lock:
                from schulmanager.server.routes.features_common import get_store
                job.status, job.applied_at = "applied", _now()
                job.applied_version = get_store().version
                job.message = "Übernommen"
            self._emit(job)
            return {"job": job.public(), "lessons": info.get("lessons", 0), "warnings": [],
                    "version": job.applied_version}

        def fn(school):
            courses = school.index("courses")
            lessons = []
            dropped = 0
            for d in lessons_data:
                le = Lesson.from_dict(d)
                c = courses.get(le.course_id)
                if c is None:
                    dropped += 1
                    continue
                n = len(c.parts)
                le.rooms = (list(le.rooms) + [None] * n)[:n]
                lessons.append(le)
            if job.params.get("period"):       # Planzeitraum: nur dessen Plan ersetzen (plan_periods.merge_generated)
                from schulmanager import plan_periods as pp
                info.update(pp.merge_generated(school, lessons, job.params["period"], job.params.get("period_keep") or []),
                            dropped=dropped)
            else:
                school.lessons = lessons
                info.update(lessons=len(lessons), dropped=dropped)
            if regenerate_duties:    # Aufsichten passen sonst nicht mehr zu den neuen Standorten/Stunden
                from schulmanager.duties import generate_duties
                school.duties = list(generate_duties(school))
                info.update(duties=len(school.duties), duties_open=sum(1 for d in school.duties if not d.teacher))
            return info

        try:
            var = f", Variante {variant + 1}" if variant is not None else ""
            mutate(user, f"Stundenplan aus Generator übernommen ({len(lessons_data)} Blöcke{var})", fn,
                   scope=["timetable", "duties"] if regenerate_duties else ["timetable"], action="plan.generator_apply",
                   details={"job": job_id, "variant": variant, "duties": regenerate_duties})
        except Exception:
            with self._lock:
                job.status = "done"
            raise
        with self._lock:
            from schulmanager.server.routes.features_common import get_store
            job.status, job.applied_at = "applied", _now()
            job.applied_version = get_store().version
            job.message = "Übernommen"
        self._emit(job)
        warnings = []
        if info.get("dropped"):
            warnings.append(f"{info['dropped']} Blöcke verworfen (Kurs existiert nicht mehr)")
        return {"job": job.public(), "lessons": info.get("lessons", 0), "warnings": warnings,
                "version": job.applied_version, "duties": info.get("duties") if regenerate_duties else None,
                "duties_open": info.get("duties_open") if regenerate_duties else None}

    # ------------------------------------------------------------ Ende
    def shutdown(self) -> None:
        """Beendet laufende Generator-Prozesse (beim Herunterfahren des Servers)."""
        for job in self.list():
            if job.status in RUNNING_STATES:
                try:
                    self.cancel(job.id)
                except JobError:
                    pass
            proc = job.process
            if proc is not None and proc.is_alive():
                proc.terminate()
                proc.join(timeout=2)

    def running_count(self) -> int:
        return 1 if self.running() else 0

    # ------------------------------------------------------------ Events
    def _emit(self, job: Job) -> None:
        try:
            from schulmanager.server.events import bus
            bus.publish("job", job.event(), permission="timetable.generate")
        except Exception:  # pragma: no cover
            log.debug("Job-Event konnte nicht gesendet werden", exc_info=True)


manager = JobManager()


def shutdown() -> None:
    manager.shutdown()


def running_count() -> int:
    """Für ``/metrics`` (``schulmanager_jobs_running``)."""
    return manager.running_count()
