"""Moodle-Datenbank (SQLite-Abzug) → :class:`~.model.Bundle`.

Gelesen werden die Tabellen aus ``public/lib/db/install.xml`` und den Modulen ``mod/assign``, ``mod/quiz``, ``mod/forum``
(Quelle: https://github.com/moodle/moodle, Stand 6.0dev). Getestet gegen das Schema ab Moodle 4.0 (Fragenbank mit
``question_bank_entries``/``question_versions``); für ältere Stände fällt der Leser auf ``quiz_slots.questionid`` zurück.

Eingabe: Pfad zu einer SQLite-Datei oder eine offene ``sqlite3``-Verbindung. Produktive Moodle-Installationen laufen auf
MySQL/MariaDB/PostgreSQL – dafür vorher einen SQLite-Abzug erzeugen (z. B. ``mysql2sqlite``) **oder** den Webservice
nutzen (siehe ``docs/IMPORT-FREMDSYSTEME.md``). Tabellenpräfix (``mdl_``) ist einstellbar.

Verhalten bei Fehlern: fehlende Tabellen/Spalten, unlesbare Zeilen und unbekannte Referenzen werden als
:class:`~.model.Problem` gemeldet; der Leser macht mit dem Rest weiter.

Passwörter (``user.password``), Sitzungs- und Token-Tabellen werden **nie** gelesen.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ... import grading
from .model import (Bundle, FAssign, FBadge, FCourse, FEnrol, FFile, FFramework, FGradeItem, FGroup, FPerson, FPost,
                    FQuestion, FQuiz, FSubmission)
from .text import clean, epoch_to_dt, epoch_to_iso, html_to_md, parse_date

BIRTH_FIELDS = {"geburtsdatum", "birthdate", "geburtstag", "dob", "birthday", "gebdatum"}
CLASS_FIELDS = {"klasse", "class", "stammklasse", "klassenname"}
TEACH_ROLES = {"editingteacher": "teacher", "teacher": "assistant"}
_PREFIX_RE = re.compile(r"^[A-Za-z0-9_]{0,30}$")


class _Q:
    """Kleiner Lesezugriff mit Präfix und Tabellen-/Spaltenprüfung."""

    def __init__(self, con: sqlite3.Connection, prefix: str):
        if not _PREFIX_RE.match(prefix):
            raise ValueError("Ungültiges Tabellenpräfix")
        self.con, self.prefix = con, prefix
        self.con.row_factory = sqlite3.Row
        self._tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        self._cols: dict[str, set[str]] = {}

    def has(self, table: str) -> bool:
        return self.prefix + table in self._tables

    def cols(self, table: str) -> set[str]:
        if table not in self._cols:
            self._cols[table] = {r[1] for r in self.con.execute(f'PRAGMA table_info("{self.prefix}{table}")')}
        return self._cols[table]

    def rows(self, table: str, where: str = "", params: tuple = (), order: str = "id") -> list[sqlite3.Row]:
        if not self.has(table):
            return []
        sql = f'SELECT * FROM "{self.prefix}{table}"' + (f" WHERE {where}" if where else "")
        if order and order in self.cols(table):
            sql += f" ORDER BY {order}"
        return self.con.execute(sql, params).fetchall()


def _g(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    try:
        v = row[key]
    except (IndexError, KeyError):
        return default
    return default if v is None else v


def _f(value: Any) -> Optional[float]:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def read_moodle_db(source: str | Path | sqlite3.Connection, *, prefix: str = "mdl_", instance: str = "standard",
                   today: Optional[datetime] = None) -> Bundle:
    own = not isinstance(source, sqlite3.Connection)
    con = sqlite3.connect(f"file:{Path(source).as_posix()}?mode=ro", uri=True) if own else source  # type: ignore[arg-type]
    try:
        return _read(_Q(con, prefix), instance, today or datetime.now(timezone.utc).replace(tzinfo=None),
                     str(source) if own else "sqlite")
    except sqlite3.DatabaseError as exc:      # keine/kaputte SQLite-Datei
        b = Bundle(system="moodle", source=Path(str(source)).name if own else "sqlite", instance=instance)
        b.problem("format", "datei", f"Keine lesbare SQLite-Datenbank: {exc}")
        return b
    finally:
        if own:
            con.close()


def _read(q: _Q, instance: str, now: datetime, source: str) -> Bundle:
    b = Bundle(system="moodle", source=Path(source).name if source != "sqlite" else source, instance=instance)
    b.info["tables"] = sum(1 for t in q._tables if t.startswith(q.prefix))
    if not q.has("user") or not q.has("course"):
        b.problem("format", "schema", f"Keine Moodle-Tabellen mit Präfix „{q.prefix}“ gefunden (Tabellen user/course fehlen)")
        return b
    steps = [("Nutzer", _users), ("Kurse", _courses), ("Einschreibungen", _enrolments), ("Gruppen", _groups),
             ("Dateien", _files), ("Aufgaben", _assigns), ("Notenbuch", _grade_items), ("Fragen", _questions),
             ("Kompetenzen", _competencies), ("Abzeichen", _badges), ("Foren", _forums)]
    ctx: dict[str, Any] = {"now": now}
    for label, fn in steps:
        try:
            fn(q, b, ctx)
        except sqlite3.Error as exc:
            b.problem("format", label, f"{label} nicht lesbar: {exc}")
    _finish(b, ctx)
    return b


# ------------------------------------------------------------------------------------------------------ Nutzer
def _users(q: _Q, b: Bundle, ctx: dict) -> None:
    fields = {r["id"]: str(r["shortname"]).lower() for r in q.rows("user_info_field")}
    birth: dict[int, str] = {}
    klass: dict[int, str] = {}
    for r in q.rows("user_info_data"):
        name = fields.get(r["fieldid"], "")
        if name in BIRTH_FIELDS:
            birth[r["userid"]] = parse_date(_g(r, "data", ""))
        elif name in CLASS_FIELDS:
            klass[r["userid"]] = clean(_g(r, "data", ""))
    users: dict[int, FPerson] = {}
    deleted = 0
    for r in q.rows("user"):
        try:
            if _g(r, "username") == "guest" or _g(r, "id") == 1 and _g(r, "username") == "guest":
                continue
            if _g(r, "deleted", 0):
                deleted += 1
                continue
            uid = int(r["id"])
            users[uid] = FPerson(
                src_id=str(uid), first=clean(_g(r, "firstname", "")), last=clean(_g(r, "lastname", "")),
                email=clean(_g(r, "email", "")).lower(), username=clean(_g(r, "username", "")),
                ident=clean(_g(r, "idnumber", "")), birth=birth.get(uid, ""),
                class_hint=klass.get(uid) or clean(_g(r, "department", "")),
                status="suspended" if _g(r, "suspended", 0) else "active")
        except (TypeError, ValueError, KeyError) as exc:
            b.problem("zeile", f"user:{_g(r, 'id', '?')}", f"Nutzerzeile unlesbar: {exc}")
    ctx["users"] = users
    b.info["users_total"] = len(users)
    b.info["users_deleted"] = deleted
    ctx["user_names"] = {uid: p.name for uid, p in users.items()}


# ------------------------------------------------------------------------------------------------------ Kurse
def _courses(q: _Q, b: Bundle, ctx: dict) -> None:
    cats = {r["id"]: clean(_g(r, "name", "")) for r in q.rows("course_categories")}
    sections: dict[int, dict[int, str]] = {}
    for r in q.rows("course_sections"):
        sections.setdefault(r["course"], {})[int(_g(r, "section", 0))] = clean(_g(r, "name", ""))
    ctx["course_ctx"] = {}
    for r in q.rows("context", "contextlevel = 50"):
        ctx["course_ctx"][r["id"]] = r["instanceid"]
    ctx["ctx_course"] = dict(ctx["course_ctx"])
    mod_ctx = {}
    for r in q.rows("context", "contextlevel = 70"):
        mod_ctx[r["id"]] = r["instanceid"]
    ctx["mod_ctx"] = mod_ctx
    ctx["cm"] = {r["id"]: r for r in q.rows("course_modules")}
    ctx["modname"] = {r["id"]: r["name"] for r in q.rows("modules")}
    for r in q.rows("course"):
        if _g(r, "category", 0) == 0 or _g(r, "format") == "site":
            continue
        cid = str(r["id"])
        b.courses[cid] = FCourse(
            src_id=cid, short=clean(_g(r, "shortname", "")), full=clean(_g(r, "fullname", "")),
            ident=clean(_g(r, "idnumber", "")), category=cats.get(_g(r, "category", 0), ""),
            start=epoch_to_iso(_g(r, "startdate", 0)), end=epoch_to_iso(_g(r, "enddate", 0)),
            hidden=not _g(r, "visible", 1), summary=html_to_md(_g(r, "summary", "")),
            sections=sections.get(r["id"], {}))


# ------------------------------------------------------------------------------------------------------ Einschreibungen
def _enrolments(q: _Q, b: Bundle, ctx: dict) -> None:
    now_ts = int(ctx["now"].replace(tzinfo=timezone.utc).timestamp())
    roles = {r["id"]: r["shortname"] for r in q.rows("role")}
    enrol = {r["id"]: r for r in q.rows("enrol")}
    course_of_ctx = ctx["course_ctx"]
    assigned: dict[tuple[int, int], set[str]] = {}      # (Kurs, Nutzer) → Rollenkürzel
    for r in q.rows("role_assignments"):
        c = course_of_ctx.get(r["contextid"])
        if c is not None:
            assigned.setdefault((c, r["userid"]), set()).add(roles.get(r["roleid"], str(r["roleid"])))
    users = ctx["users"]
    seen: set[tuple[int, int]] = set()
    for r in q.rows("user_enrolments"):
        e = enrol.get(r["enrolid"])
        if e is None:
            b.problem("referenz", f"user_enrolments:{r['id']}", "Einschreibemethode fehlt")
            continue
        cid, uid = e["courseid"], r["userid"]
        if str(cid) not in b.courses or uid not in users:
            continue
        seen.add((cid, uid))
        end = _g(r, "timeend", 0)
        active = (not _g(r, "status", 0) and not _g(e, "status", 0) and (not end or end > now_ts))
        note = "" if active else ("abgelaufen" if end and end <= now_ts else "ausgesetzt")
        rs = assigned.get((cid, uid)) or ({roles.get(_g(e, "roleid", 0), "student")} if _g(e, "roleid", 0) else {"student"})
        if (cid, uid) not in assigned:
            note = (note + "; " if note else "") + "ohne Rollenzuweisung (als Rolle der Einschreibemethode)"
        mapped = {TEACH_ROLES.get(x, "student" if x == "student" else "") for x in rs}
        mapped.discard("")
        for role in sorted(mapped) or ["other"]:
            if role == "other":
                continue
            b.enrols.append(FEnrol(str(cid), str(uid), role, active, note))
    for (cid, uid), rs in assigned.items():          # Lehrkräfte ohne Einschreibung
        if (cid, uid) in seen or str(cid) not in b.courses or uid not in users:
            continue
        for x in rs:
            if x in TEACH_ROLES:
                b.enrols.append(FEnrol(str(cid), str(uid), TEACH_ROLES[x], True, "ohne Einschreibung"))
    enrolled = {e.person for e in b.enrols}
    teachers = {e.person for e in b.enrols if e.role in ("teacher", "assistant")}
    for uid, p in list(users.items()):
        sid = str(uid)
        if sid in enrolled:
            p.role = "teacher" if sid in teachers else "student"
            b.persons[sid] = p
    b.info["users_without_course"] = len(users) - len(b.persons)


# ------------------------------------------------------------------------------------------------------ Gruppen
def _groups(q: _Q, b: Bundle, ctx: dict) -> None:
    members: dict[int, list[str]] = {}
    for r in q.rows("groups_members"):
        members.setdefault(r["groupid"], []).append(str(r["userid"]))
    grouping_of: dict[int, str] = {}
    gnames = {r["id"]: clean(_g(r, "name", "")) for r in q.rows("groupings")}
    for r in q.rows("groupings_groups"):
        grouping_of[r["groupid"]] = gnames.get(r["groupingid"], "")
    for r in q.rows("groups"):
        if str(r["courseid"]) not in b.courses:
            continue
        b.groups.append(FGroup(str(r["id"]), str(r["courseid"]), clean(_g(r, "name", "")),
                               [m for m in members.get(r["id"], []) if m in b.persons], grouping_of.get(r["id"], "")))


# ------------------------------------------------------------------------------------------------------ Dateien
def _files(q: _Q, b: Bundle, ctx: dict) -> None:
    ctx["files_by_sub"] = {}
    if not q.has("files"):
        return
    for r in q.rows("files"):
        name = _g(r, "filename", "")
        if name in ("", "."):                    # Verzeichniseinträge
            continue
        comp, area = _g(r, "component", ""), _g(r, "filearea", "")
        if area in ("draft", "private", "backup") or comp in ("user", "backup"):
            continue
        cid = ctx["course_ctx"].get(r["contextid"])
        if cid is None and r["contextid"] in ctx["mod_ctx"]:
            cm = ctx["cm"].get(ctx["mod_ctx"][r["contextid"]])
            cid = _g(cm, "course") if cm is not None else None
        f = FFile(str(r["id"]), clean(name), _g(r, "mimetype", "") or "", int(_g(r, "filesize", 0) or 0),
                  str(cid) if cid is not None else "", f"{comp}/{area}", str(_g(r, "userid", "") or ""), str(_g(r, "itemid", "")))
        if comp == "assignsubmission_file":
            ctx["files_by_sub"].setdefault(int(_g(r, "itemid", 0)), []).append(f)
        elif f.course in b.courses:
            b.files.append(f)


# ------------------------------------------------------------------------------------------------------ Aufgaben
def _assigns(q: _Q, b: Bundle, ctx: dict) -> None:
    modid = next((i for i, n in ctx["modname"].items() if n == "assign"), None)
    cm_by_inst = {int(_g(cm, "instance", 0)): cm for cm in ctx["cm"].values() if _g(cm, "module") == modid}
    sec_no = {r["id"]: int(_g(r, "section", 0)) for r in q.rows("course_sections")}
    ctx["assign_cm"] = {}
    text_of = {r["submission"]: r for r in q.rows("assignsubmission_onlinetext")}
    fb_of = {r["grade"]: r for r in q.rows("assignfeedback_comments")}
    subs_by: dict[int, list] = {}
    for r in q.rows("assign_submission"):
        subs_by.setdefault(r["assignment"], []).append(r)
    grades_by: dict[tuple[int, int, int], Any] = {}
    for r in q.rows("assign_grades"):
        grades_by[(r["assignment"], r["userid"], int(_g(r, "attemptnumber", 0)))] = r
    rubrics = _rubrics(q, b, ctx)
    scales = {r["id"]: [s.strip() for s in str(_g(r, "scale", "")).split(",")] for r in q.rows("scale")}
    for a in q.rows("assign"):
        cid = str(a["course"])
        if cid not in b.courses:
            continue
        cm = cm_by_inst.get(a["id"])
        if cm is not None:
            ctx["assign_cm"][a["id"]] = cm
        top = _f(_g(a, "grade", 0)) or 0.0
        fa = FAssign(src_id=str(a["id"]), course=cid, title=clean(_g(a, "name", "")) or f"Aufgabe {a['id']}",
                     intro=html_to_md(_g(a, "intro", "")), due=epoch_to_dt(_g(a, "duedate", 0)),
                     cutoff=epoch_to_dt(_g(a, "cutoffdate", 0)), max_points=top if top > 0 else None,
                     section=sec_no.get(_g(cm, "section"), 0) if cm is not None else 0,
                     visible=bool(_g(cm, "visible", 1)) if cm is not None else True,
                     team=bool(_g(a, "teamsubmission", 0)), no_submission=bool(_g(a, "nosubmissions", 0)))
        scale_labels = scales.get(abs(int(top))) if top < 0 else None
        rub = rubrics.get(cm["id"]) if cm is not None else None
        if rub:
            fa.rubric = rub["rubric"]
        # Abgaben: je Person die letzte Version
        rows = subs_by.get(a["id"], [])
        group_rows = {r["groupid"]: r for r in rows if not r["userid"] and _g(r, "groupid", 0)
                      and _g(r, "latest", 0)}
        latest: dict[int, Any] = {}
        for r in rows:
            if not r["userid"]:
                continue
            cur = latest.get(r["userid"])
            if cur is None or (_g(r, "latest", 0), _g(r, "attemptnumber", 0)) > (_g(cur, "latest", 0), _g(cur, "attemptnumber", 0)):
                latest[r["userid"]] = r
        fa.skipped_attempts = len(rows) - len(latest) - len(group_rows)
        member_group = {}
        if fa.team:
            for g in b.groups:
                if g.course == cid:
                    for m in g.members:
                        member_group.setdefault(int(m), g)
        for uid, r in latest.items():
            pid = str(uid)
            if pid not in b.persons or b.persons[pid].role != "student":
                continue
            src_row, gid = r, ""
            if fa.team and uid in member_group:
                gr = group_rows.get(int(member_group[uid].src_id))
                if gr is not None:
                    src_row, gid = gr, member_group[uid].src_id
            status = _g(src_row, "status", "")
            att = int(_g(r, "attemptnumber", 0))
            grade = grades_by.get((a["id"], uid, att)) or grades_by.get((a["id"], uid, int(_g(src_row, "attemptnumber", 0))))
            gval = _f(_g(grade, "grade", None)) if grade is not None else None
            if gval is not None and gval < 0:
                gval = None
            text_row = text_of.get(src_row["id"])
            text = html_to_md(_g(text_row, "onlinetext", "")) if text_row is not None else ""
            files = ctx["files_by_sub"].get(int(src_row["id"]), [])
            if status in ("new", "reopened") or (status == "draft" and gval is None):
                if status == "draft":
                    b.problem("nicht_unterstuetzt", f"assign:{a['id']}:user:{uid}", "Entwurf (nicht abgegeben) übersprungen")
                continue
            if status not in ("submitted", "draft") and gval is None:
                continue
            sub = FSubmission(person=pid, status="abgegeben", text=text,
                              at=epoch_to_dt(_g(src_row, "timemodified", 0)), attempt=att + 1, files=files, group=gid)
            if fa.due and sub.at and sub.at > fa.due:
                sub.status = "verspätet"
            if grade is not None and gval is not None:
                sub.graded_at = epoch_to_dt(_g(grade, "timemodified", 0))
                sub.status = "bewertet"
                sub.points, sub.max_points = gval, fa.max_points
                fb = fb_of.get(grade["id"])
                if fb is not None:
                    sub.feedback = html_to_md(_g(fb, "commenttext", ""))
                if rub and grade["id"] in rub["fills"]:
                    fill, score = rub["fills"][grade["id"]]
                    sub.rubric_fill = fill
                    sub.points, sub.max_points = score, grading.max_points(rub["rubric"])
            elif scale_labels and grade is not None:
                pass
            fa.submissions.append(sub)
        b.assigns.append(fa)


def _rubrics(q: _Q, b: Bundle, ctx: dict) -> dict:
    """``{Kurs-Modul-ID: {"rubric": normalisiertes Raster, "fills": {assign_grades.id: (fill, Punktsumme)}}}``."""
    out: dict = {}
    if not q.has("grading_areas") or not q.has("gradingform_rubric_criteria"):
        return out
    areas = {r["id"]: r for r in q.rows("grading_areas") if _g(r, "component") == "mod_assign"}
    defs = {r["areaid"]: r for r in q.rows("grading_definitions") if _g(r, "method") == "rubric" and _g(r, "status", 0) in (20, 10)}
    crit_by: dict[int, list] = {}
    for r in q.rows("gradingform_rubric_criteria", order="sortorder, id"):
        crit_by.setdefault(r["definitionid"], []).append(r)
    lev_by: dict[int, list] = {}
    for r in q.rows("gradingform_rubric_levels", order="score, id"):
        lev_by.setdefault(r["criterionid"], []).append(r)
    inst_by: dict[int, list] = {}
    for r in q.rows("grading_instances"):
        if _g(r, "status", 0) == 1:
            inst_by.setdefault(r["definitionid"], []).append(r)
    fills_by: dict[int, list] = {}
    for r in q.rows("gradingform_rubric_fillings"):
        fills_by.setdefault(r["instanceid"], []).append(r)
    for area_id, area in areas.items():
        d = defs.get(area_id)
        if d is None:
            continue
        cm = area["contextid"]
        cm_id = ctx["mod_ctx"].get(cm)
        raw = {"kind": "rubric", "criteria": []}
        score_of: dict[int, float] = {}
        for c in crit_by.get(d["id"], []):
            lv = [{"id": f"l{x['id']}", "title": html_to_md(_g(x, "definition", "")) or f"{_g(x, 'score', 0):g} Punkte",
                   "points": float(_g(x, "score", 0))} for x in lev_by.get(c["id"], [])]
            for x in lev_by.get(c["id"], []):
                score_of[x["id"]] = float(_g(x, "score", 0))
            raw["criteria"].append({"id": f"c{c['id']}", "title": html_to_md(_g(c, "description", "")) or f"Kriterium {c['id']}",
                                    "levels": lv})
        try:
            rubric = grading.normalize_rubric(raw)
        except ValueError as exc:
            b.problem("nicht_unterstuetzt", f"rubric:{d['id']}", f"Bewertungsraster „{_g(d, 'name', '')}“ nicht übernehmbar: {exc}")
            continue
        fills: dict[int, tuple] = {}
        for inst in inst_by.get(d["id"], []):
            fill, score = {}, 0.0
            for f in fills_by.get(inst["id"], []):
                if _g(f, "levelid") is None:
                    continue
                fill[f"c{f['criterionid']}"] = {"level": f"l{f['levelid']}", "comment": html_to_md(_g(f, "remark", ""))}
                score += score_of.get(f["levelid"], 0.0)
            fills[inst["itemid"]] = (fill, score)        # itemid = assign_grades.id
        if cm_id is not None:
            out[cm_id] = {"rubric": rubric, "fills": fills, "title": clean(_g(d, "name", ""))}
    return out


# ------------------------------------------------------------------------------------------------------ Notenbuch
def _grade_items(q: _Q, b: Bundle, ctx: dict) -> None:
    scales = {r["id"]: [s.strip() for s in str(_g(r, "scale", "")).split(",")] for r in q.rows("scale")}
    cats = {r["id"]: clean(_g(r, "fullname", "")) for r in q.rows("grade_categories")}
    results: dict[int, list] = {}
    for r in q.rows("grade_grades"):
        results.setdefault(r["itemid"], []).append(r)
    assign_ids = {a.src_id for a in b.assigns}
    quiz_titles = {r["id"]: r for r in q.rows("quiz")}
    for it in q.rows("grade_items"):
        typ = _g(it, "itemtype", "")
        cid = str(_g(it, "courseid", ""))
        if typ in ("course", "category") or cid not in b.courses:
            continue
        gtype = int(_g(it, "gradetype", 1))
        if gtype not in (1, 2):
            continue
        module = _g(it, "itemmodule", "")
        if typ == "mod" and module not in ("assign", "quiz"):
            continue
        kind = module if typ == "mod" else ("scale" if gtype == 2 else "manual")
        scale = scales.get(_g(it, "scaleid", 0) or 0, []) if gtype == 2 else []
        fi = FGradeItem(src_id=str(it["id"]), course=cid, title=clean(_g(it, "itemname", "")) or f"Bewertung {it['id']}",
                        kind=kind, max_points=_f(_g(it, "grademax", None)) if gtype == 1 else None, scale=scale,
                        date=epoch_to_iso(_g(it, "timecreated", 0)), category=cats.get(_g(it, "categoryid", 0), ""),
                        link=str(_g(it, "iteminstance", "")) if typ == "mod" else "")
        if kind == "quiz" and _g(it, "iteminstance") in quiz_titles:
            fi.title = fi.title or clean(quiz_titles[it["iteminstance"]]["name"])
        for r in results.get(it["id"], []):
            pid = str(r["userid"])
            if pid not in b.persons or b.persons[pid].role != "student":
                continue
            val = _f(_g(r, "finalgrade", None))
            if val is None:
                val = _f(_g(r, "rawgrade", None))
            if val is None:
                continue
            text = ""
            if gtype == 2:
                idx = int(round(val)) - 1
                if 0 <= idx < len(scale):
                    text = scale[idx]
                else:
                    b.problem("referenz", f"grade_grades:{r['id']}", f"Skalenwert {val:g} außerhalb der Skala")
                    continue
                fi.results[pid] = (None, text)
            else:
                fi.results[pid] = (val, "")
        if fi.kind == "assign" and fi.link not in assign_ids:
            continue
        b.grade_items.append(fi)


# ------------------------------------------------------------------------------------------------------ Fragen/Quiz
def _questions(q: _Q, b: Bundle, ctx: dict) -> None:
    if not q.has("quiz"):
        return
    modid = next((i for i, n in ctx["modname"].items() if n == "quiz"), None)
    cm_by_inst = {int(_g(cm, "instance", 0)): cm for cm in ctx["cm"].values() if _g(cm, "module") == modid}
    sec_no = {r["id"]: int(_g(r, "section", 0)) for r in q.rows("course_sections")}
    questions = {r["id"]: r for r in q.rows("question")}
    versions: dict[int, list] = {}
    for r in q.rows("question_versions"):
        versions.setdefault(r["questionbankentryid"], []).append(r)
    refs: dict[int, list] = {}
    for r in q.rows("question_references"):
        if _g(r, "component") == "mod_quiz" and _g(r, "questionarea") == "slot":
            refs.setdefault(r["itemid"], []).append(r)
    answers: dict[int, list] = {}
    for r in q.rows("question_answers"):
        answers.setdefault(r["question"], []).append(r)
    opts = {r["questionid"]: r for r in q.rows("qtype_multichoice_options")}
    tf = {r["question"]: r for r in q.rows("question_truefalse")}
    sa = {r["questionid"]: r for r in q.rows("qtype_shortanswer_options")}
    num = {r["question"]: r for r in q.rows("question_numerical")}
    subq: dict[int, list] = {}
    for r in q.rows("qtype_match_subquestions"):
        subq.setdefault(r["questionid"], []).append(r)
    slots: dict[int, list] = {}
    for r in q.rows("quiz_slots", order="slot"):
        slots.setdefault(r["quizid"], []).append(r)
    legacy = "questionid" in q.cols("quiz_slots")
    for z in q.rows("quiz"):
        cid = str(z["course"])
        if cid not in b.courses:
            continue
        cm = cm_by_inst.get(z["id"])
        fq = FQuiz(src_id=str(z["id"]), course=cid, title=clean(_g(z, "name", "")) or f"Test {z['id']}",
                   intro=html_to_md(_g(z, "intro", "")),
                   time_limit_min=(int(_g(z, "timelimit", 0)) // 60) or None,
                   max_attempts=int(_g(z, "attempts", 0)) or None, opens=epoch_to_dt(_g(z, "timeopen", 0)),
                   closes=epoch_to_dt(_g(z, "timeclose", 0)),
                   section=sec_no.get(_g(cm, "section"), 0) if cm is not None else 0,
                   visible=bool(_g(cm, "visible", 1)) if cm is not None else True)
        for slot in slots.get(z["id"], []):
            qrow, entry = None, None
            if legacy and _g(slot, "questionid"):
                qrow = questions.get(slot["questionid"])
                entry = f"q{slot['questionid']}"
            else:
                for ref in refs.get(slot["id"], []):
                    entry = str(ref["questionbankentryid"])
                    vs = sorted(versions.get(ref["questionbankentryid"], []), key=lambda v: v["version"])
                    ready = [v for v in vs if _g(v, "status", "ready") == "ready"]
                    pick = None
                    if _g(ref, "version") is not None:
                        pick = next((v for v in vs if v["version"] == ref["version"]), None)
                    if pick is None and ready:
                        pick = ready[-1]
                    if pick is not None:
                        qrow = questions.get(pick["questionid"])
                    break
            if qrow is None or entry is None:
                b.problem("referenz", f"quiz:{z['id']}:slot:{slot['id']}", "Frage zum Platz nicht gefunden")
                continue
            fq.questions.append(entry)
            if entry not in b.questions:
                b.questions[entry] = _translate(qrow, cid, entry, _f(_g(slot, "maxmark", None)), answers, opts, tf, sa, num, subq)
        b.quizzes.append(fq)


def _translate(qr, cid: str, entry: str, mark: Optional[float], answers, opts, tf, sa, num, subq) -> FQuestion:
    qtype = _g(qr, "qtype", "")
    title = clean(_g(qr, "name", ""))
    fq = FQuestion(entry, cid, qtype, title)
    text = html_to_md(_g(qr, "questiontext", ""))
    base: dict[str, Any] = {"text": text or title, "points": min(mark if mark is not None else (_f(_g(qr, "defaultmark", 1)) or 1.0), 100.0),
                            "feedback": html_to_md(_g(qr, "generalfeedback", ""))}
    ans = answers.get(qr["id"], [])
    if qtype == "multichoice":
        single = bool(_g(opts.get(qr["id"]), "single", 1)) if qr["id"] in opts else True
        best = max((_f(a["fraction"]) or 0.0 for a in ans), default=0.0)
        options = []
        for a in ans:
            fr = _f(a["fraction"]) or 0.0
            correct = (fr >= best - 1e-6 and fr > 0) if single else fr > 0
            options.append({"text": html_to_md(a["answer"]), "correct": correct, "feedback": html_to_md(_g(a, "feedback", ""))})
        fq.data = {**base, "type": "single" if single else "multi", "options": options}
    elif qtype == "truefalse":
        t = tf.get(qr["id"])
        if t is None:
            fq.reason = "Richtig/Falsch ohne Lösung"
        else:
            fq.data = {**base, "type": "truefalse", "correct": t["trueanswer"] in {a["id"] for a in ans if (_f(a["fraction"]) or 0) > 0.99}}
    elif qtype == "shortanswer":
        good = [html_to_md(a["answer"]) for a in ans if (_f(a["fraction"]) or 0) > 0 and "*" not in a["answer"]]
        if not good:
            fq.reason = "Kurzantwort nur mit Platzhaltern (*)"
        else:
            body = base["text"] if "___" in base["text"] else base["text"] + " ___"
            fq.data = {**base, "text": body, "type": "cloze", "gaps": [good],
                       "case_sensitive": bool(_g(sa.get(qr["id"]), "usecase", 0))}
    elif qtype == "numerical":
        n = num.get(qr["id"])
        first = next((a for a in ans if (_f(a["fraction"]) or 0) >= 0.99), None)
        try:
            value = float(str(first["answer"]).replace(",", ".")) if first is not None else None
        except ValueError:
            value = None
        if value is None:
            fq.reason = "Numerische Frage ohne lesbare Lösung"
        else:
            fq.data = {**base, "type": "numeric", "value": value, "tolerance": _f(_g(n, "tolerance", 0)) if n is not None else 0.0}
    elif qtype == "match":
        pairs = [{"left": html_to_md(s["questiontext"]), "right": clean(s["answertext"])} for s in subq.get(qr["id"], [])
                 if clean(_g(s, "questiontext", "")) and clean(_g(s, "answertext", ""))]
        fq.data = {**base, "type": "matching", "pairs": pairs}
    else:
        fq.reason = f"Fragetyp „{qtype}“ wird nicht unterstützt"
    return fq


# ------------------------------------------------------------------------------------------------------ Kompetenzen
def _competencies(q: _Q, b: Bundle, ctx: dict) -> None:
    if not q.has("competency_framework") or not q.has("competency"):
        return
    scales = {r["id"]: [s.strip() for s in str(_g(r, "scale", "")).split(",") if s.strip()] for r in q.rows("scale")}
    comps: dict[int, list] = {}
    for r in q.rows("competency", order="sortorder, id"):
        comps.setdefault(r["competencyframeworkid"], []).append(r)
    course_links: dict[int, list[str]] = {}
    for r in q.rows("competency_coursecomp"):
        course_links.setdefault(r["competencyid"], []).append(str(r["courseid"]))
    evid_note: dict[int, str] = {}
    for r in q.rows("competency_evidence"):
        if _g(r, "note"):
            evid_note[r["usercompetencyid"]] = html_to_md(r["note"])
    user_comps: dict[int, list] = {}
    for r in q.rows("competency_usercomp"):
        user_comps.setdefault(r["competencyid"], []).append(r)
    for fw in q.rows("competency_framework"):
        levels = scales.get(_g(fw, "scaleid", 0) or 0) or []
        proficient_at = None
        try:
            cfg = json.loads(_g(fw, "scaleconfiguration", "") or "[]")
            for entry in cfg:
                if isinstance(entry, dict) and entry.get("proficient") and "id" in entry and proficient_at is None:
                    proficient_at = int(entry["id"])
        except (ValueError, TypeError):
            pass
        rows = comps.get(fw["id"], [])
        by_parent: dict[int, list] = {}
        for r in rows:
            by_parent.setdefault(int(_g(r, "parentid", 0)), []).append(r)
        f = FFramework(src_id=str(fw["id"]), name=clean(_g(fw, "shortname", "")) or f"Rahmen {fw['id']}",
                       description=html_to_md(_g(fw, "description", ""))[:500], levels=levels,
                       support_level=max(1, (proficient_at or 3) - 1))
        loose: list[dict] = []

        def leaf(r, prefix: str = "") -> dict:
            return {"src_id": str(r["id"]), "code": clean(_g(r, "idnumber", ""))[:20],
                    "title": (prefix + (clean(_g(r, "shortname", "")) or html_to_md(_g(r, "description", ""))))[:300],
                    "descriptors": []}

        for top in by_parent.get(0, []):
            kids = by_parent.get(top["id"], [])
            if not kids:
                loose.append(leaf(top))
                continue
            area = {"name": clean(_g(top, "shortname", "")) or "Bereich", "competencies": []}
            stack = list(kids)
            while stack:
                k = stack.pop(0)
                area["competencies"].append(leaf(k))
                for sub in by_parent.get(k["id"], []):      # tiefere Ebenen flach anhängen
                    c = leaf(sub, clean(_g(k, "shortname", "")) + " › ")
                    area["competencies"].append(c)
            f.areas.append(area)
        if loose:
            f.areas.append({"name": "Allgemein", "competencies": loose})
        cids = set()
        for r in rows:
            for cid in course_links.get(r["id"], []):
                cids.add(cid)
            for uc in user_comps.get(r["id"], []):
                pid = str(uc["userid"])
                lvl = _g(uc, "grade")
                if pid in b.persons and lvl:
                    f.assessments.append((pid, str(r["id"]), int(lvl), epoch_to_iso(_g(uc, "timemodified", 0) or _g(uc, "timecreated", 0)),
                                          evid_note.get(uc["id"], "")))
        f.courses = sorted(c for c in cids if c in b.courses)
        if f.levels and len(f.levels) >= 2:
            b.frameworks.append(f)
        else:
            b.problem("nicht_unterstuetzt", f"competency_framework:{fw['id']}", "Kompetenzrahmen ohne lesbare Skala (mind. 2 Stufen)")


# ------------------------------------------------------------------------------------------------------ Abzeichen
def _badges(q: _Q, b: Bundle, ctx: dict) -> None:
    issued: dict[int, list] = {}
    for r in q.rows("badge_issued"):
        issued.setdefault(r["badgeid"], []).append(r)
    for r in q.rows("badge"):
        cid = str(_g(r, "courseid", "") or "")
        bd = FBadge(src_id=str(r["id"]), name=clean(_g(r, "name", ""), 100) or f"Abzeichen {r['id']}",
                    description=clean(_g(r, "description", ""), 300), course=cid if cid in b.courses else "",
                    active=int(_g(r, "status", 0)) in (1, 3))
        for i in issued.get(r["id"], []):
            pid = str(i["userid"])
            if pid in b.persons:
                bd.awards.append((pid, epoch_to_iso(_g(i, "dateissued", 0))))
        b.badges.append(bd)


# ------------------------------------------------------------------------------------------------------ Foren
def _forums(q: _Q, b: Bundle, ctx: dict) -> None:
    if not q.has("forum_posts"):
        return
    forums = {r["id"]: r for r in q.rows("forum")}
    disc = {r["id"]: r for r in q.rows("forum_discussions")}
    names = ctx["user_names"]
    for p in q.rows("forum_posts", order="created, id"):
        d = disc.get(p["discussion"])
        if d is None or _g(p, "deleted", 0):
            continue
        cid = str(d["course"])
        if cid not in b.courses:
            continue
        f = forums.get(d["forum"])
        b.posts.append(FPost(str(p["id"]), cid, clean(_g(f, "name", "Forum")) if f is not None else "Forum",
                             clean(_g(p, "subject", "")), html_to_md(_g(p, "message", "")),
                             names.get(p["userid"], "Unbekannt"), epoch_to_dt(_g(p, "created", 0)),
                             str(p["parent"]) if _g(p, "parent", 0) else ""))


def _finish(b: Bundle, ctx: dict) -> None:
    b.info["suspended"] = sum(1 for p in b.persons.values() if p.status == "suspended")
    b.info["inactive_enrolments"] = sum(1 for e in b.enrols if not e.active)
