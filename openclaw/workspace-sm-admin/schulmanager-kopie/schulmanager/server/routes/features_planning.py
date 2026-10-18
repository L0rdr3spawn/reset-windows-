"""Planung: Kurse aus Stundentafeln, Lehrerzuweisung, Qualitätsbericht,
Stundenplan-Generierung (Hintergrund-Job), Neuplanung für eine Lehrkraft und Pausenaufsichten."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import cached, has, mutate, need, parse_date, reads_all_plans, snapshot

router = APIRouter(tags=["Planung"])


class GenerateIn(BaseModel):
    time_limit: Optional[float] = Field(None, ge=1, le=3600, description="Rechenzeit in Sekunden")
    keep_locked: bool = True
    seed: int = Field(1, ge=0, le=2**31 - 1)
    workers: int = Field(0, ge=0, le=16, description="Parallele Läufe (0 = automatisch, 1 = einer)")
    variants: int = Field(1, ge=1, le=5, description="Anzahl Varianten (nacheinander, je mit eigenem Startwert)")
    # Probelauf mit ungespeicherten Regeln (``settings.rules``-Form): Der Entwurf rechnet mit diesen Regeln, die
    # Einstellungen der Schule bleiben unverändert; Übernehmen des Entwurfs geht wie sonst über den Job.
    rules: Optional[dict] = Field(None, description="Regeln und Prioritäten nur für diesen Lauf (Vorher/Nachher)")
    # Planzeitraum (``schulmanager/plan_periods.py``, Kennung): Der Entwurf gilt nach dem Übernehmen nur für diesen
    # Zeitraum; ``copy_from`` = Plan eines anderen Zeitraums als fixierter Start (nur Lücken werden neu geplant)
    period: Optional[str] = Field(None, max_length=20, description="Zeitraum, für den der Plan gerechnet wird")
    copy_from: Optional[str] = Field(None, max_length=20, description="Zeitraum, dessen Plan als Start dient")


class ReplanIn(BaseModel):
    time_limit: Optional[float] = Field(None, ge=1, le=600, description="Rechenzeit in Sekunden (Standard 15)")
    seed: int = Field(1, ge=0, le=2**31 - 1)
    scope: Literal["teacher", "classes"] = Field(
        "teacher", description="teacher = nur Stunden der Lehrkraft frei; classes = auch alle Stunden ihrer Klassen")
    workers: int = Field(1, ge=0, le=16)


def _jobs():
    from schulmanager.server.jobs import JobError, manager
    return manager, JobError


def _job_error(exc) -> HTTPException:
    return HTTPException(getattr(exc, "status", 409), str(exc))


class CoursesFromCurriculaIn(BaseModel):
    dry_run: bool = Field(False, description="nur Vorschau (nichts speichern)")
    reset_manual: bool = Field(False, description="eigene Anpassungen an Stundentafel-Kursen verwerfen")


def _rebuild(school, reset_manual: bool) -> dict:
    from schulmanager.planning import rebuild_courses
    before = len(school.courses)
    out = rebuild_courses(school, reset_manual=reset_manual)
    valid = {c.id for c in school.courses}
    dropped = [le.id for le in school.lessons if le.course_id not in valid]
    if dropped:
        school.lessons = [le for le in school.lessons if le.course_id in valid]
        gone = set(dropped)
        school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
    removed = set(out["removed"])
    if removed:   # „Unterricht findet nicht statt“ entfernter Kurse (ref „<kurs>“ bzw. „<kurs>#<teil>“)
        school.absences = [a for a in school.absences
                           if not (a.kind == "lesson" and str(a.ref).split("#", 1)[0] in removed)]
        exams = [e.id for e in school.exams if e.course_id in removed]
        if exams:
            out["warnings"].append(f"Klausuren verweisen auf entfernte Kurse: {', '.join(exams[:20])}")
    out.update({"courses": len(school.courses), "before": before, "removed_lessons": len(dropped)})
    out["replan_needed"] = bool(out["replan_needed"] or dropped)
    return out


@router.post("/planning/courses-from-curricula")
def courses_from_curricula(body: Optional[CoursesFromCurriculaIn] = None,
                           user: AuthUser = Depends(require("timetable.edit"))):
    """Erzeugt Kurse aus den Stundentafeln (vorhandene Kopplungen werden angerechnet, eigene Anpassungen an
    Stundentafel-Kursen bleiben erhalten). ``dry_run`` = Vorschau mit Liste neuer/entfernter/geänderter Kurse."""
    from schulmanager.server.store import copy_school
    body = body or CoursesFromCurriculaIn()
    if body.dry_run:
        out = _rebuild(copy_school(snapshot()[1]), body.reset_manual)
        out["dry_run"] = True
        return out

    def fn(school):
        out = _rebuild(school, body.reset_manual)
        out["dry_run"] = False
        return out

    return mutate(user, "Kurse aus Stundentafeln erzeugt", fn, scope=["courses", "timetable"])


@router.get("/planning/curricula/overview")
def curricula_overview(user: AuthUser = Depends(current_user)):
    """Welche Stundentafel gilt für welche Klasse (Klasse vor Jahrgang), Konflikte, Klassen ohne Tafel."""
    if not (reads_all_plans(user) or user.has("timetable.edit") or user.has("timetable.generate")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()

    def compute():
        from schulmanager.planning import curriculum_overview
        out = curriculum_overview(snap[1])
        out["version"] = snap[0]
        return out

    return cached("curricula_overview", (), compute, snap)


@router.post("/planning/assign-teachers")
def assign_teachers(user: AuthUser = Depends(require("timetable.edit"))):
    """Weist offenen Kursteilen qualifizierte Lehrkräfte zu."""
    from schulmanager.planning import assign_teachers as _assign

    def fn(school):
        open_before = sum(1 for c in school.courses for p in c.parts if not p.teacher)
        warnings = _assign(school)
        open_after = sum(1 for c in school.courses for p in c.parts if not p.teacher)
        return {"warnings": warnings, "assigned": open_before - open_after, "open": open_after}

    return mutate(user, "Lehrkräfte zugewiesen", fn, scope=["courses"])


@router.get("/planning/report")
def report(user: AuthUser = Depends(current_user)):
    """Qualitätsbericht: ``timetable.validate_school`` + Kapazitätswarnungen (schulweit – nicht für Lehrkräfte)."""
    if not (reads_all_plans(user) or user.has("timetable.edit") or user.has("timetable.generate")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()

    def compute():
        from schulmanager.planning import capacity_warnings
        from schulmanager.timetable import validate_school
        out = dict(validate_school(snap[1]))
        out["capacity_warnings"] = capacity_warnings(snap[1])
        out["open_parts"] = [
            {"course": c.id, "label": c.label or c.id, "part": i, "subject": p.subject}
            for c in snap[1].courses for i, p in enumerate(c.parts) if not p.teacher
        ][:500]
        out["version"] = snap[0]
        return out

    return cached("planning_report", (), compute, snap)


@router.get("/planning/report/details")
def report_details(kind: Optional[Literal["class_gaps", "teacher_gaps", "site_changes", "commute", "conflicts",
                                          "core_late", "unplaced", "overplaced", "teachers", "weeks"]] = None,
                   user: AuthUser = Depends(current_user)):
    """Einzelne Fundstellen hinter den Kennzahlen des Qualitätsberichts (Hohl-/Springstunden mit Tag und Stunde,
    Konflikte, unverplante Stunden mit Grund, Lehrkräfte mit Deputat …). Ohne ``kind`` alle Listen. Nur lesend –
    ändert nichts am Stundenplan."""
    if not (reads_all_plans(user) or user.has("timetable.edit") or user.has("timetable.generate")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()

    def compute():
        from schulmanager.timetable import validate_school
        out = validate_school(snap[1], details=True)
        return {"details": out["details"], "ranges": out["ranges"], "stats": out["stats"], "version": snap[0]}

    full = cached("planning_report_details", (), compute, snap)
    if kind is None:
        return full
    return {"kind": kind, "items": full["details"][kind], "ranges": full["ranges"], "stats": full["stats"],
            "version": full["version"]}


def _period_input(school, data: dict, body: GenerateIn, params: dict) -> dict:
    """Generator-Eingabe für einen Planzeitraum (``plan_periods.prepare_generation``); ergänzt ``params``."""
    from schulmanager import plan_periods as pp
    from schulmanager.models import School
    if not body.period or not pp.active(school) or pp.get(school, body.period) is None:
        raise HTTPException(422, "Bitte einen Zeitraum wählen (Planung › Zeitraster & Schuljahr).")
    work = School.from_dict(data)
    try:
        info = pp.prepare_generation(work, body.period, body.copy_from or "")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    params["period"], params["period_keep"] = body.period, info["keep"]
    if body.copy_from:
        params["copy_from"] = body.copy_from
    return work.to_dict()


@router.post("/planning/generate", status_code=202)
def generate(body: Optional[GenerateIn] = None, user: AuthUser = Depends(require("timetable.generate"))):
    """Startet die Stundenplan-Generierung als Hintergrundprozess → ``{job_id}``."""
    from schulmanager.server.config import config
    body = body or GenerateIn()
    manager, JobError = _jobs()
    ver, school = snapshot()
    if not school.courses:
        raise HTTPException(409, "Keine Kurse vorhanden – zuerst Kurse aus den Stundentafeln erzeugen")
    limit = body.time_limit if body.time_limit is not None else float(config.generate_time_limit or 30)
    params = {"time_limit": float(limit), "keep_locked": body.keep_locked, "seed": body.seed,
              "workers": body.workers, "variants": body.variants, "evaluate": True}
    data = school.to_dict()
    if body.rules is not None:
        from schulmanager import rules as rl
        from schulmanager.server.store import copy_school
        errs = rl.rule_errors(body.rules, school)
        if errs:
            raise HTTPException(422, "; ".join(errs))
        probe = copy_school(school)
        rl.apply_to_settings(probe.settings, body.rules)
        data = probe.to_dict()
        params["rules_preview"] = True
    if body.period or body.copy_from:
        data = _period_input(school, data, body, params)
    try:
        job = manager.start_generate(data, params, user=user, base_version=ver)
    except JobError as exc:
        raise _job_error(exc) from None
    return {"job_id": job.id, "job": job.public()}


@router.post("/planning/replan-teacher/{teacher_id}", status_code=202)
def replan_teacher(teacher_id: str, body: Optional[ReplanIn] = None,
                   user: AuthUser = Depends(require("timetable.generate"))):
    """Neuplanung für eine Lehrkraft (z. B. nach geänderten Zeitfenstern): alle übrigen Stunden bleiben fixiert,
    Ergebnis als Entwurf (``GET /planning/jobs/{id}``, Übernahme mit ``POST /planning/jobs/{id}/apply``)."""
    from schulmanager.server.config import config
    from schulmanager.server.jobs import prepare_replan
    body = body or ReplanIn()
    manager, JobError = _jobs()
    ver, school = snapshot()
    from schulmanager import plan_periods as pp
    if pp.active(school):
        raise HTTPException(409, "Mit Planzeiträumen planen Sie im Generator je Zeitraum neu "
                                 "(Planung › Generator, Zeitraum wählen).")
    teacher = school.index("teachers").get(teacher_id)
    if teacher is None:
        raise HTTPException(404, f"Lehrkraft {teacher_id} nicht gefunden")
    try:
        school_dict, context = prepare_replan(school, teacher_id, body.scope)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    limit = body.time_limit if body.time_limit is not None else min(15.0, float(config.generate_time_limit or 15))
    params = {"time_limit": float(limit), "keep_locked": True, "seed": body.seed, "workers": body.workers,
              "teacher_id": teacher_id, "teacher_name": teacher.name, "scope": body.scope,
              "free_courses": len(context["free_courses"])}
    try:
        job = manager.start_generate(school_dict, params, user=user, base_version=ver, kind="replan_teacher",
                                     context=context)
    except JobError as exc:
        raise _job_error(exc) from None
    return {"job_id": job.id, "job": job.public()}


def _autoplan_status() -> dict:
    from schulmanager.autoplan import find_problems
    from schulmanager.server.autoplan import planner

    out = planner.status()
    ver, school = snapshot()
    problems = find_problems(school)
    out["version"] = ver
    out["setting"] = bool(getattr(school.settings, "auto_replan", True))
    out["open_problems"] = problems.summary(school, limit=30)
    out["open_count"] = problems.count()
    out["auto_apply"] = getattr(school.settings, "plan_auto_apply", "aus")
    try:
        from schulmanager.server import proposals
        out["proposals"] = proposals.summary()
    except Exception:  # noqa: BLE001 - Anzeige ist optional
        out["proposals"] = None
    return out


@router.get("/planning/autoplan")
def autoplan_status(user: AuthUser = Depends(current_user)):
    """Dauerprüfung: Status, letzte automatische Änderung (nur mit ``plan_auto_apply``) und offene Probleme des
    Stundenplans; Vorschläge siehe ``/planning/proposals``."""
    need(user, "timetable.generate", "timetable.edit")
    return _autoplan_status()


@router.post("/planning/autoplan/run")
def autoplan_run(user: AuthUser = Depends(require("timetable.generate"))):
    """Dauerprüfung sofort ausführen und die Vorschläge neu berechnen (auch für Probleme, die verworfen wurden)."""
    from schulmanager.server.autoplan import planner
    if not planner.enabled:
        raise HTTPException(409, "Der Auto-Planer ist auf diesem Server abgeschaltet (SM_AUTOPLAN=0)")
    planner.run_now()
    return _autoplan_status()


@router.get("/planning/jobs")
def list_jobs(user: AuthUser = Depends(current_user)):
    need(user, "timetable.generate", "timetable.edit")
    manager, _ = _jobs()
    return [j.public() for j in manager.list()]


@router.get("/planning/jobs/{job_id}")
def get_job(job_id: str, lessons: bool = False, user: AuthUser = Depends(current_user)):
    """Status/Entwurf eines Jobs (``?lessons=1`` liefert auch die Stunden des Entwurfs)."""
    need(user, "timetable.generate", "timetable.edit")
    manager, _ = _jobs()
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(404, "Job nicht gefunden")
    out = job.public(with_lessons=lessons)
    ver = snapshot()[0]
    out["outdated"] = job.base_version is not None and job.base_version != ver and job.status == "done"
    return out


@router.post("/planning/jobs/{job_id}/cancel")
def cancel_job(job_id: str, user: AuthUser = Depends(require("timetable.generate"))):
    manager, JobError = _jobs()
    try:
        return manager.cancel(job_id).public()
    except JobError as exc:
        raise _job_error(exc) from None


@router.delete("/planning/jobs/{job_id}")
def delete_job(job_id: str, user: AuthUser = Depends(require("timetable.generate"))):
    """Bricht einen laufenden Job ab (Alias zu ``/cancel``)."""
    return cancel_job(job_id, user)


class ApplyIn(BaseModel):
    variant: Optional[int] = Field(None, ge=0, le=4, description="Nummer der Variante (ohne Angabe: die beste)")
    regenerate_duties: bool = Field(True, description="Pausenaufsichten für den neuen Plan neu berechnen")


@router.post("/planning/jobs/{job_id}/apply")
def apply_job(job_id: str, body: Optional[ApplyIn] = None, user: AuthUser = Depends(require("timetable.generate"))):
    """Übernimmt den Entwurf (bzw. eine Variante) als neuen Stundenplan (neue Version, Undo möglich). Standardmäßig
    werden die Pausenaufsichten gleich neu berechnet (``duties.generate_duties``)."""
    body = body or ApplyIn()
    manager, JobError = _jobs()
    try:
        variant = body.variant
        if variant is None and (manager.get(job_id) and (manager.get(job_id).result or {}).get("variants")):
            variant = manager.get(job_id).result.get("best_variant", 0)
        return manager.apply(job_id, user, variant=variant, regenerate_duties=body.regenerate_duties)
    except JobError as exc:
        raise _job_error(exc) from None


def _variant(job_id: str, index: int) -> dict:
    manager, JobError = _jobs()
    try:
        return manager.variant_of(job_id, index)
    except JobError as exc:
        raise _job_error(exc) from None


@router.get("/planning/jobs/{job_id}/variants/{index}")
def job_variant(job_id: str, index: int, user: AuthUser = Depends(current_user)):
    """Auswertung einer Variante: Kennzahlen vorher/nachher, Klassen/Lehrkräfte, Verschiebungen, Verteilung, Regeln,
    Hinweise und Verlauf der Optimierung (ohne die Stunden selbst)."""
    need(user, "timetable.generate", "timetable.edit")
    v = _variant(job_id, index)
    return {"index": v["index"], "seed": v["seed"], "stats": v["stats"], "evaluation": v["evaluation"],
            "trace": v.get("trace", []), "runs": v.get("runs", []), "unplaced": v["unplaced"]}


@router.get("/planning/jobs/{job_id}/variants/{index}/timetable/{kind}/{ref}")
def job_variant_timetable(job_id: str, index: int, kind: str, ref: str,
                          date_: Optional[str] = Query(None, alias="date"), all_days: bool = Query(True),
                          user: AuthUser = Depends(current_user)):
    """Wochenraster einer Variante (wie ``/timetable/{kind}/{ref}``); nichts wird gespeichert."""
    need(user, "timetable.generate", "timetable.edit")
    if kind not in ("class", "teacher", "room"):
        raise HTTPException(422, "Nur Klasse, Lehrkraft oder Raum")
    v = _variant(job_id, index)
    from datetime import date as _date

    from schulmanager.calendar_utils import monday_of
    from schulmanager.models import Lesson, School
    from schulmanager.timetable import timetable_view
    school = School.from_dict(snapshot()[1].to_dict())
    school.lessons = [Lesson.from_dict(d) for d in v["lessons"]]
    day = parse_date(date_, _date.today())
    try:
        return timetable_view(school, kind, ref, when=monday_of(day), all_days=all_days)
    except KeyError as exc:
        raise HTTPException(404, str(exc.args[0]) if exc.args else "Nicht gefunden") from None


class ClearIn(BaseModel):
    period: Optional[str] = Field(None, max_length=20, description="Zeitraum, dessen Plan geleert wird")
    all: bool = Field(False, description="Ausdrücklich den ganzen Plan (alle Zeiträume) leeren")


@router.post("/planning/clear")
def clear_plan(body: Optional[ClearIn] = None, user: AuthUser = Depends(require("timetable.generate"))):
    """„Plan leeren“: entfernt Unterrichtsblöcke samt Tagesentscheidungen. Kurse, Lehrkräfte und Räume bleiben.
    Mit eingerichteten Planzeiträumen muss ``period`` (nur dieser Zeitraum, ``plan_periods.clear_period``) oder
    ausdrücklich ``all`` angegeben werden. Der bisherige Stand bleibt als Version erhalten (Rückgängig über „Verlauf“)."""
    from schulmanager import plan_periods as pp
    body = body or ClearIn()
    info: dict = {}

    def fn(school):
        if pp.active(school) and not body.all:
            if not body.period:
                raise HTTPException(422, "Bitte einen Zeitraum wählen oder ausdrücklich den ganzen Plan leeren")
            if pp.get(school, body.period) is None:
                raise HTTPException(404, "Zeitraum nicht gefunden")
            info.update(lessons=pp.clear_period(school, body.period), period=body.period)
            return info
        info["lessons"] = len(school.lessons)
        gone = {le.id for le in school.lessons}
        school.lessons = []
        school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
        return info

    what = "Plan geleert (alle Unterrichtsblöcke entfernt)"
    if body.period and not body.all:
        what = f"Plan des Zeitraums „{body.period}“ geleert"
    mutate(user, what, fn, scope=["timetable"], action="plan.clear",
           details={"period": body.period or "", "all": body.all})
    return info


@router.post("/duties/generate")
def generate_duties(user: AuthUser = Depends(require("timetable.edit"))):
    """Erzeugt die Pausenaufsichten neu (faire Verteilung, ``duties.generate_duties``)."""
    from schulmanager.duties import generate_duties as _gen

    def fn(school):
        duties = _gen(school)
        school.duties = list(duties)
        open_ = sum(1 for d in school.duties if not d.teacher)
        return {"duties": len(school.duties), "open": open_}

    return mutate(user, "Pausenaufsichten erzeugt", fn, scope=["duties"])


@router.get("/duties/overview")
def duties_overview(date_: Optional[str] = Query(None, alias="date"), user: AuthUser = Depends(current_user)):
    """Aufsichtsplan der Woche (Tag × Pause × Bereich) mit Namen, Standort der Lehrkräfte, Konflikten und
    Ersatzvorschlägen (``duties.duty_overview``). Nur für Planung/Vertretungsplanung; Lehrkräfte sehen ihre Aufsichten
    über die Sammlung ``duties``."""
    if not (has(user, "timetable.edit") or has(user, "substitution.edit")):
        raise HTTPException(403, "Keine Berechtigung")
    day = parse_date(date_)
    snap = snapshot()

    def compute():
        from schulmanager.duties import duty_overview
        return duty_overview(snap[1], day)

    return cached("duty_overview", (day.isoformat(),), compute, snap)
