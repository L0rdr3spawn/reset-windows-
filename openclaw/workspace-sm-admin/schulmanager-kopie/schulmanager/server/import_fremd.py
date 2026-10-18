"""Importe aus Fremdsystemen anwenden: Zuordnung, Trockenlauf, Idempotenz, Protokoll, Rückgängig.

Die Leser (``schulmanager/integrations/fremd/*``) liefern ein neutrales :class:`~schulmanager.integrations.fremd.model.Bundle`;
dieses Modul schreibt es in Planungsdokument (``School``) und Datenbank.

Einstieg für Oberfläche/Einrichtungsassistent
---------------------------------------------
::

    from schulmanager.integrations.fremd import registry
    from schulmanager.server import import_fremd as imp

    bundle, info = registry.read_bundle(files={"name.sqlite": bytes}, system="auto")   # erkennt das Format
    opts = imp.Options.from_dict({"instance": "moodle-schule", "create_missing_students": True,
                                  "course_map": {"7": "M-5a#0"}, "person_map": {"31": "S0004"}})
    report = imp.run_import(db, user, bundle, opts, dry_run=True)       # Vorschau, schreibt nichts
    report = imp.run_import(db, user, bundle, opts, dry_run=False)      # echter Lauf, Commit macht der Aufrufer
    imp.undo_run(db, user, report["run_id"])                            # alles zurück, was dieser Lauf angelegt hat

``report["needs_decision"]`` listet, was die Verwaltung noch entscheiden muss (Kurs ohne Zuordnung, mehrdeutige Person);
die Antworten kommen als ``course_map``/``person_map`` zurück. Ein zweiter Lauf mit derselben Quelle erzeugt keine
Dubletten: jedes Quell-Element hat eine Verknüpfung (``import_links``), unveränderte Elemente werden übersprungen.

Schreibweg: Stammdaten (Klassen, Schüler/innen, Lehrkräfte) über ``store.mutate`` (neue Version, Undo im Verlauf),
alles andere in die Tabellen der Kursräume, Aufgaben, Selbsttests, Kompetenzen, Notenbuch-Quellen. Personenbezogene
Freitexte werden wie im Bestand verschlüsselt (``write_text``). Schüler/innen **ohne Konto** können weder Mitglied eines
Kursraums noch Abgebende sein – ihre Daten zählen als „wartet auf Konto“ und werden beim nächsten Lauf ergänzt.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..integrations._common import grade_from_name
from ..integrations.fremd import match as pmatch
from ..integrations.fremd.model import Bundle, FCourse, FPerson
from ..integrations.fremd.text import fold
from ..models import School, SchoolClass, Student, Teacher
from . import assignment_tools as at
from . import gradebook_sources as gs
from .audit import audit
from .import_fremd_rooms import RoomsMixin
from .db import utcnow
from .db_models import User
from .feature_models.channel_groups import ChannelGroup, ChannelGroupMember
from .feature_models.channels import (AssignmentSubmission, Channel, ChannelExtraMember, ChannelFolder, ChannelItem,
                                      ChannelPost)
from .feature_models.competency import CompAssessment, CompBadge, CompBadgeAward, CompFramework
from .feature_models.import_fremd import ImportLink, ImportRun
from .feature_models.learning import LearningQuestion, LearningSelftest

log = logging.getLogger("schulmanager.import_fremd")

PARTS = ("personen", "kursraeume", "gruppen", "aufgaben", "noten", "fragen", "kompetenzen", "abzeichen", "forum",
         "dateien")
ID_PREFIX = {"moodle": "MDL", "oneroster": "OR", "webuntis": "WU", "iserv": "IS", "schild": "SC", "asv": "ASV",
             "lusd": "LU", "csv": "CSV"}
MAX_PROBLEMS = 400
GERMAN_GRADE_WORDS = {"sehr gut": "1", "gut": "2", "befriedigend": "3", "ausreichend": "4", "mangelhaft": "5",
                      "ungenügend": "6", "ungenuegend": "6"}


class ImportError_(Exception):
    """Fachlicher Fehler eines Imports (Text für die Verwaltung)."""


@dataclass
class Options:
    instance: str = "standard"
    create_missing_students: bool = False
    create_missing_teachers: bool = False
    default_class: str = ""
    course_map: dict[str, str] = field(default_factory=dict)       # Quell-Kurs → "kurs#teil" | "neu" | "ueberspringen"
    person_map: dict[str, str] = field(default_factory=dict)       # Quell-Person → Ziel-ID (Schüler/Lehrkraft)
    include_hidden_courses: bool = True
    publish: bool = False                                          # False: Aufgaben versteckt, Selbsttests als Entwurf
    parts: tuple[str, ...] = PARTS
    only_courses: tuple[str, ...] = ()
    update_existing: bool = True                                    # leere Felder (Geburtsdatum, E-Mail) ergänzen

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "Options":
        d = data or {}
        o = cls()
        o.instance = re.sub(r"[^A-Za-z0-9_.:-]", "", str(d.get("instance") or "standard"))[:60] or "standard"
        for k in ("create_missing_students", "create_missing_teachers", "include_hidden_courses", "publish",
                  "update_existing"):
            if k in d:
                setattr(o, k, bool(d[k]))
        o.default_class = str(d.get("default_class") or "")[:40]
        o.course_map = {str(k): str(v) for k, v in (d.get("course_map") or {}).items()}
        o.person_map = {str(k): str(v) for k, v in (d.get("person_map") or {}).items()}
        parts = d.get("parts")
        if parts:
            o.parts = tuple(p for p in parts if p in PARTS)
        o.only_courses = tuple(str(x) for x in (d.get("only_courses") or ()))
        return o

    def to_dict(self) -> dict:
        return {"instance": self.instance, "create_missing_students": self.create_missing_students,
                "create_missing_teachers": self.create_missing_teachers, "default_class": self.default_class,
                "course_map": self.course_map, "person_map": self.person_map, "publish": self.publish,
                "include_hidden_courses": self.include_hidden_courses, "parts": list(self.parts),
                "only_courses": list(self.only_courses), "update_existing": self.update_existing}


def _fp(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def _utc(dt: Optional[datetime]) -> Optional[datetime]:
    return dt


class Importer(RoomsMixin):
    """Ein Lauf. Reihenfolge: Personen/Klassen (Planungsdokument) → je Kurs (Savepoint) → Kompetenzen/Abzeichen."""

    def __init__(self, db: Session, user: Any, bundle: Bundle, opts: Options, *, dry_run: bool):
        self.db, self.user, self.b, self.o, self.dry = db, user, bundle, opts, dry_run
        self.system = bundle.system
        self.run: Optional[ImportRun] = None
        self.cnt: dict[str, Counter] = defaultdict(Counter)
        self.problems: list[dict] = [{"kind": p.kind, "ref": p.ref, "message": p.message} for p in bundle.problems]
        self.notes: list[str] = []
        self.links: dict[tuple[str, str], ImportLink] = {}
        self._link_log: list[tuple[str, str]] = []
        self.person_target: dict[str, tuple[str, str]] = {}      # src → (student|teacher, id)
        self.matches: dict[str, pmatch.Match] = {}
        self.users_by_student: dict[str, int] = {}
        self.users_by_teacher: dict[str, int] = {}
        self.course_target: dict[str, dict] = {}
        self.waiting: Counter = Counter()
        self.needs_decision: list[dict] = []
        self.person_report: dict[str, Any] = {}
        self.school: School = School()
        self.new_students: list[str] = []
        self.new_teachers: list[str] = []
        self.new_classes: list[str] = []

    # ------------------------------------------------------------------ Hilfen
    def problem(self, kind: str, ref: str, message: str) -> None:
        if len(self.problems) < MAX_PROBLEMS * 4:
            self.problems.append({"kind": kind, "ref": str(ref), "message": message})

    def want(self, part: str) -> bool:
        return part in self.o.parts

    def load_links(self) -> None:
        rows = self.db.scalars(select(ImportLink).where(ImportLink.system == self.system,
                                                        ImportLink.instance == self.o.instance))
        for r in rows:
            self.links[(r.kind, r.source_key)] = r

    def link(self, kind: str, key: str) -> Optional[ImportLink]:
        return self.links.get((kind, str(key)))

    def put_link(self, kind: str, key: str, target_kind: str, target_id: Any, fp: str = "") -> tuple[ImportLink, bool]:
        key = str(key)[:120]
        row = self.links.get((kind, key))
        if row is not None:
            row.target_kind, row.target_id, row.fingerprint = target_kind, str(target_id), fp
            row.updated_run = self.run.id if self.run else None
            return row, False
        row = ImportLink(system=self.system, instance=self.o.instance, kind=kind, source_key=key,
                         target_kind=target_kind, target_id=str(target_id), fingerprint=fp,
                         created_run=self.run.id if self.run else None, created_at=utcnow())
        self.db.add(row)
        self.links[(kind, key)] = row
        self._link_log.append((kind, key))
        return row, True

    def count(self, kind: str, what: str, n: int = 1) -> None:
        self.cnt[kind][what] += n

    # ------------------------------------------------------------------ Personen und Klassen
    def phase_school(self, school: School) -> None:
        """Wird auf der Arbeitskopie (Trockenlauf) bzw. in ``store.mutate`` (echt) ausgeführt."""
        self.school = school
        self.new_students, self.new_teachers, self.new_classes = [], [], []
        self.person_target = {}
        self._classes(school)
        self._masters(school)
        if not self.want("personen"):
            return
        persons = [p for p in self.b.persons.values() if p.role in ("student", "teacher")]
        students = [pmatch.Target("student", s.id, s.name, s.class_id, s.birth_date or "") for s in school.students]
        teachers = [pmatch.Target("teacher", t.id, t.name, "", "", t.email or "") for t in school.teachers]
        accounts = [(e or "", sid or "", tid or "") for e, sid, tid in
                    self.db.execute(select(User.email, User.student_id, User.teacher_id).where(
                        (User.student_id.is_not(None)) | (User.teacher_id.is_not(None))))]
        links = {k[1]: (r.target_kind, r.target_id) for k, r in self.links.items() if k[0] == "person"}
        self.matches = pmatch.match_persons(persons, students, teachers, accounts, links, self.o.person_map)
        st_idx = {s.id: s for s in school.students}
        te_idx = {t.id: t for t in school.teachers}
        by = Counter()
        unmatched, ambiguous, conflicts, unsure = [], [], [], []
        for p in persons:
            m = self.matches[p.src_id]
            if m.status in ("matched", "linked"):
                by[m.via] += 1
                self.person_target[p.src_id] = (m.kind, m.target)
                self.count("person", "unchanged" if m.status == "linked" else "matched")
                if self.o.update_existing:
                    self._fill_existing(p, m, st_idx, te_idx)
                continue
            if m.status == "ambiguous":
                ambiguous.append(self._person_entry(p, m))
                self.needs_decision.append({"type": "person", "src": p.src_id, "name": p.name,
                                            "candidates": m.candidates, "why": "mehrdeutig"})
                continue
            if m.status == "unsure":
                unsure.append(self._person_entry(p, m))
                self.needs_decision.append({"type": "person", "src": p.src_id, "name": p.name,
                                            "candidates": m.candidates, "why": m.note})
                continue
            if m.status == "conflict":
                conflicts.append(self._person_entry(p, m))
            created = self._create_person(school, p, st_idx, te_idx)
            if created:
                self.person_target[p.src_id] = created
                self.count("person", "created")
            else:
                unmatched.append(self._person_entry(p, m))
        self.person_report = {"total": len(persons), "by": dict(by), "unmatched": unmatched[:200],
                              "unmatched_count": len(unmatched), "ambiguous": ambiguous[:200],
                              "ambiguous_count": len(ambiguous), "conflicts": conflicts[:200],
                              "conflict_count": len(conflicts), "unsure": unsure[:200], "unsure_count": len(unsure)}

    def _person_entry(self, p: FPerson, m: pmatch.Match) -> dict:
        return {"src": p.src_id, "name": p.name, "role": p.role, "email": p.email, "class": p.class_hint,
                "status": m.status, "candidates": m.candidates, "note": m.note or ""}

    def _fill_existing(self, p: FPerson, m: pmatch.Match, st_idx: dict, te_idx: dict) -> None:
        if m.kind == "student":
            s = st_idx.get(m.target)
            if s is not None and p.birth and not s.birth_date:
                s.birth_date = p.birth
                self.count("person", "updated")
        else:
            t = te_idx.get(m.target)
            if t is not None and p.email and not t.email:
                t.email = p.email
                self.count("person", "updated")

    def _classes(self, school: School) -> None:
        known = {fold(c.id): c for c in school.classes}
        known.update({fold(c.name): c for c in school.classes})
        for c in self.b.classes:
            cid = str(c.get("id") or c.get("name") or "").strip()
            name = str(c.get("name") or cid).strip()
            if not cid or fold(cid) in known or fold(name) in known:
                if cid:
                    self.count("class", "unchanged")
                continue
            grade = c.get("grade")
            grade = int(grade) if str(grade).isdigit() else grade_from_name(name)
            if grade is None:
                self.problem("zeile", f"class:{cid}", f"Klasse „{name}“: Jahrgang nicht erkennbar – nicht angelegt")
                continue
            obj = SchoolClass(cid[:40], name[:80], int(grade))
            school.classes.append(obj)
            known[fold(cid)] = obj
            self.new_classes.append(obj.id)
            self.count("class", "created")

    def _masters(self, school: School) -> None:
        """Fächer und Räume (WebUntis u. a.): vorhandene bleiben unverändert."""
        from ..models import Room, Subject
        subj = {fold(s.id) for s in school.subjects} | {fold(s.name) for s in school.subjects}
        for s in self.b.subjects:
            sid = str(s.get("id") or "").strip()
            if sid and fold(sid) not in subj and fold(s.get("name", "")) not in subj:
                school.subjects.append(Subject(sid[:20], str(s.get("name") or sid)[:80]))
                subj.add(fold(sid))
                self.count("subject", "created")
            elif sid:
                self.count("subject", "unchanged")
        rooms = {fold(r.id) for r in school.rooms}
        for r in self.b.rooms:
            rid = str(r.get("id") or "").strip()
            if rid and fold(rid) not in rooms:
                school.rooms.append(Room(rid[:20], str(r.get("name") or rid)[:80], "Standard"))
                rooms.add(fold(rid))
                self.count("room", "created")
            elif rid:
                self.count("room", "unchanged")

    def _find_class(self, school: School, hint: str) -> Optional[str]:
        h = fold(hint)
        if h:
            for c in school.classes:
                if fold(c.id) == h or fold(c.name) == h:
                    return c.id
        if self.o.default_class and any(c.id == self.o.default_class for c in school.classes):
            return self.o.default_class
        return None

    def _create_person(self, school: School, p: FPerson, st_idx: dict, te_idx: dict) -> Optional[tuple[str, str]]:
        prefix = ID_PREFIX.get(self.system, "FS")
        if p.role == "student" and self.o.create_missing_students:
            cls = self._find_class(school, p.class_hint)
            if not cls:
                self.problem("referenz", f"person:{p.src_id}", f"{p.name}: keine passende Klasse „{p.class_hint}“ "
                             "(bitte Standardklasse angeben) – nicht angelegt")
                return None
            sid = self._free_id(p.ident, f"{prefix}{p.src_id}", st_idx)
            obj = Student(sid, p.name, cls, birth_date=p.birth or None)
            school.students.append(obj)
            st_idx[sid] = obj
            self.new_students.append(sid)
            return "student", sid
        if p.role == "teacher" and self.o.create_missing_teachers:
            code = p.ident if p.ident and len(p.ident) <= 10 else (fold(p.last)[:3].upper() or "LK")
            tid = self._free_id(code, f"{prefix}{p.src_id}", te_idx, short=True)
            obj = Teacher(tid, p.name, [], email=p.email or "")
            school.teachers.append(obj)
            te_idx[tid] = obj
            self.new_teachers.append(tid)
            return "teacher", tid
        return None

    @staticmethod
    def _free_id(wish: str, fallback: str, taken: dict, short: bool = False) -> str:
        base = re.sub(r"[^A-Za-z0-9_.-]", "", wish or "")[:30]
        for cand in ([base] if base else []) + [fallback]:
            if cand and cand not in taken:
                return cand
        n = 2
        stem = base or fallback
        while f"{stem}{n}" in taken:
            n += 1
        return f"{stem}{n}"

    # ------------------------------------------------------------------ Konten
    def load_accounts(self) -> None:
        for uid, sid, tid in self.db.execute(select(User.id, User.student_id, User.teacher_id).where(
                (User.student_id.is_not(None)) | (User.teacher_id.is_not(None)))):
            if sid:
                self.users_by_student.setdefault(sid, uid)
            if tid:
                self.users_by_teacher.setdefault(tid, uid)

    def user_of(self, person_src: str) -> Optional[int]:
        t = self.person_target.get(person_src)
        if not t:
            return None
        return (self.users_by_student if t[0] == "student" else self.users_by_teacher).get(t[1])

    def student_of(self, person_src: str) -> Optional[str]:
        t = self.person_target.get(person_src)
        return t[1] if t and t[0] == "student" else None

    # ------------------------------------------------------------------ Kurs-Zuordnung
    def resolve_courses(self) -> None:
        school = self.school
        by_id = {fold(c.id): c for c in school.courses}
        for c in self.b.courses.values():
            if self.o.only_courses and c.src_id not in self.o.only_courses:
                continue
            info = {"src": c.src_id, "title": c.title, "short": c.short, "hidden": c.hidden, "mode": "", "ref": "",
                    "candidates": [], "why": ""}
            if c.hidden and not self.o.include_hidden_courses:
                info.update(mode="skip", why="versteckter Kurs")
                self.course_target[c.src_id] = info
                continue
            choice = self.o.course_map.get(c.src_id)
            lk = self.link("course", c.src_id)
            if choice:
                low = choice.lower()
                if low in ("ueberspringen", "skip", "überspringen"):
                    info.update(mode="skip", why="von der Verwaltung übersprungen")
                elif low in ("neu", "new", "custom"):
                    info.update(mode="custom", why="als eigener Kursraum (Entscheidung)")
                else:
                    ref = choice if "#" in choice else f"{choice}#0"
                    cid, _, part = ref.rpartition("#")
                    course = next((x for x in school.courses if x.id == cid), None)
                    if course is not None and part.isdigit() and int(part) < len(course.parts):
                        info.update(mode="mapped", ref=ref, why="von der Verwaltung zugeordnet")
                    else:
                        info.update(mode="custom", why=f"Zuordnung {choice!r} unbekannt – als eigener Kursraum")
                        self.problem("referenz", f"course:{c.src_id}", f"Zuordnung {choice!r} nicht gefunden")
            elif lk is not None and lk.target_kind == "channel":
                info.update(mode="linked", why="früherer Import")
            else:
                found = None
                for key in (c.ident, c.short):
                    if key and fold(key) in by_id:
                        found = by_id[fold(key)]
                        break
                if found is not None and len(found.parts) == 1:
                    info.update(mode="mapped", ref=f"{found.id}#0", why="Kürzel entspricht dem Kurs")
                elif found is not None:
                    info.update(mode="custom", why="Kurs hat mehrere Teile – bitte Teil wählen",
                                candidates=[f"{found.id}#{i}" for i in range(len(found.parts))])
                    self.needs_decision.append({"type": "course", "src": c.src_id, "title": c.title,
                                                "candidates": info["candidates"], "why": "mehrere Kursteile"})
                else:
                    cands = self._course_candidates(c)
                    info.update(mode="custom", candidates=cands,
                                why="keine eindeutige Zuordnung – wird als eigener Kursraum angelegt")
                    self.needs_decision.append({"type": "course", "src": c.src_id, "title": c.title,
                                                "candidates": cands, "why": "keine Zuordnung"})
            self.course_target[c.src_id] = info

    def _course_candidates(self, c: FCourse) -> list[str]:
        title = fold(c.title + " " + c.short)
        scored: list[tuple[int, str]] = []
        for course in self.school.courses:
            for i, part in enumerate(course.parts):
                score = 0
                if any(fold(cl) and fold(cl) in title for cl in course.classes):
                    score += 2
                subj = next((s for s in self.school.subjects if s.id == part.subject), None)
                if fold(part.subject) and fold(part.subject) in title:
                    score += 1
                if subj is not None and fold(subj.name) and fold(subj.name) in title:
                    score += 2
                if score >= 3:
                    scored.append((score, f"{course.id}#{i}"))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [r for _, r in scored[:4]]

    # ------------------------------------------------------------------ Lauf
    def start_run(self, source_name: str, source_hash: str) -> None:
        self.run = ImportRun(system=self.system, instance=self.o.instance, source_name=source_name[:200],
                             source_hash=source_hash, user_id=getattr(self.user, "id", None) or None,
                             user_name=(getattr(self.user, "username", "") or "")[:80], started_at=utcnow(),
                             status="ok", options=self.o.to_dict(), summary=None, report_enc="", undone_by="")
        self.db.add(self.run)
        self.db.flush()

    def link_persons(self, created: dict[str, tuple[str, str]]) -> None:
        for src, (kind, tid) in self.person_target.items():
            old = self.link("person", src)
            new_kind = f"{kind}_created" if src in created else kind
            if old is not None and old.target_id == tid:
                new_kind = old.target_kind
            self.put_link("person", src, new_kind, tid)
        for cid in self.new_classes:
            self.put_link("class", cid, "class_created", cid)

    def report(self) -> dict:
        problems = self.problems
        kinds = Counter(p["kind"] for p in problems)
        lines = self.summary_lines()
        return {
            "system": self.system, "instance": self.o.instance, "dry_run": self.dry,
            "run_id": self.run.id if self.run else None, "source": self.b.source,
            "bundle": self.b.counts(), "info": self.b.info, "persons": self.person_report,
            "courses": list(self.course_target.values()),
            "counts": {k: dict(v) for k, v in self.cnt.items()},
            "waiting_for_accounts": dict(self.waiting),
            "needs_decision": self.needs_decision,
            "problems": problems[:MAX_PROBLEMS], "problem_count": len(problems), "problem_kinds": dict(kinds),
            "notes": self.notes[:100], "lines": lines,
            "status": "teilweise" if kinds.get("fehler") else "ok"}

    def summary_lines(self) -> list[str]:
        verb = {"created": "neu", "updated": "aktualisiert", "unchanged": "unverändert", "skipped": "übersprungen",
                "matched": "zugeordnet"}
        label = {"person": "Personen", "class": "Klassen", "course": "Kurse/Kursräume", "member": "Mitglieder",
                 "subject": "Fächer", "room": "Räume", "group": "Gruppen", "group_member": "Gruppenmitglieder", "folder": "Ordner", "assign": "Aufgaben",
                 "submission": "Abgaben", "question": "Fragen", "selftest": "Selbsttests",
                 "grade_item": "Notenbuch-Quellen", "file": "Dateien (Platzhalter)", "post": "Forenbeiträge",
                 "framework": "Kompetenzrahmen", "assessment": "Lernstände", "badge": "Abzeichen",
                 "award": "Abzeichen-Vergaben"}
        out = []
        for k, name in label.items():
            c = self.cnt.get(k)
            if c:
                out.append(f"{name}: " + ", ".join(f"{n} {verb[w]}" for w, n in c.items() if n))
        for key, text in (("members", "Kursraum-Mitglieder"), ("submissions", "Abgaben"), ("grades", "Noten"),
                          ("group_members", "Gruppenmitglieder"), ("assessments", "Lernstände")):
            if self.waiting.get(key):
                out.append(f"{self.waiting[key]} {text} warten auf ein Konto der Person (nach dem Anlegen der Konten "
                           "erneut importieren)")
        return out


def run_import(db: Session, user: Any, bundle: Bundle, opts: Optional[Options] = None, *, dry_run: bool = True,
               source_name: str = "", source_hash: str = "") -> dict:
    """Import ausführen oder (``dry_run``) nur berechnen. Rückgabe: Bericht (siehe Modul-Doku). Commit macht der Aufrufer.

    Im Trockenlauf läuft derselbe Code wie im echten Lauf; alle Datenbankänderungen werden am Ende verworfen, das
    Planungsdokument wird nur als Kopie verändert – die Vorschau stimmt deshalb mit dem echten Ergebnis überein."""
    from .store import copy_school, get_store
    opts = opts or Options()
    imp = Importer(db, user, bundle, opts, dry_run=dry_run)
    store = get_store()
    guard = db.begin_nested() if dry_run else None
    created: dict[str, tuple[str, str]] = {}
    try:
        imp.load_links()
        imp.load_accounts()
        if dry_run:
            imp.phase_school(copy_school(store.school))
        else:
            # Zuerst das Planungsdokument (eigene Transaktion des Stores), erst danach schreibt diese Sitzung –
            # sonst sperren sich beide Schreiber (SQLite).
            def apply_school(sc: School) -> None:
                imp.phase_school(sc)

            store.mutate(user, f"Import aus {bundle.system} ({opts.instance})", apply_school,
                         scope=["students", "teachers", "classes", "import"])
            imp.start_run(source_name or bundle.source, source_hash)
        created = {src: v for src, v in imp.person_target.items()
                   if v[1] in imp.new_students or v[1] in imp.new_teachers}
        imp.resolve_courses()
        if any(p in opts.parts for p in ("kursraeume", "aufgaben", "noten", "fragen", "gruppen", "dateien", "forum")):
            imp.apply_courses()
        if "kompetenzen" in opts.parts:
            imp.apply_frameworks()
        if "abzeichen" in opts.parts:
            imp.apply_badges()
        if not dry_run:
            imp.link_persons(created)
    except Exception:
        if guard is not None:
            guard.rollback()
        raise
    if dry_run:
        assert guard is not None
        guard.rollback()
        return imp.report()
    rep = imp.report()
    run = imp.run
    assert run is not None
    run.finished_at, run.status = utcnow(), rep["status"]
    run.summary = {"counts": rep["counts"], "waiting": rep["waiting_for_accounts"], "problems": rep["problem_count"]}
    run.write_text("report", json.dumps(rep, ensure_ascii=False, default=str))
    audit(db, user, "import.fremd", f"run:{run.id}",
          {"system": bundle.system, "instance": opts.instance, "counts": rep["counts"], "problems": rep["problem_count"],
           "waiting": rep["waiting_for_accounts"]})
    db.flush()
    return rep


# ===================================================================================== Protokoll
def run_dict(r: ImportRun, *, with_report: bool = False) -> dict:
    d = {"id": r.id, "system": r.system, "instance": r.instance, "source": r.source_name, "user": r.user_name,
         "started_at": r.started_at.isoformat() if r.started_at else None,
         "finished_at": r.finished_at.isoformat() if r.finished_at else None, "status": r.status,
         "summary": r.summary or {}, "undone_at": r.undone_at.isoformat() if r.undone_at else None,
         "undone_by": r.undone_by}
    if with_report:
        raw = r.read_text("report")
        try:
            d["report"] = json.loads(raw) if raw else None
        except ValueError:
            d["report"] = None
        d["options"] = r.options or {}
    return d


def list_runs(db: Session, limit: int = 50) -> list[dict]:
    rows = db.scalars(select(ImportRun).order_by(ImportRun.id.desc()).limit(min(max(limit, 1), 200)))
    return [run_dict(r) for r in rows]


# ===================================================================================== Rückgängig
def undo_run(db: Session, user: Any, run_id: int) -> dict:
    """Entfernt alles, was dieser Lauf **neu angelegt** hat (Kursräume, Aufgaben samt Abgaben, Selbsttests, Gruppen,
    Mitglieder, Foren-Beiträge, Kompetenzrahmen, Abzeichen, Notenbuch-Quellen, neue Schüler/innen/Lehrkräfte/Klassen).
    Was der Lauf nur **geändert** hat (aktualisierte Texte, ergänzte Geburtsdaten), bleibt, wie es ist."""
    from .store import get_store
    run = db.get(ImportRun, run_id)
    if run is None:
        raise ImportError_("Importlauf nicht gefunden")
    if run.undone_at is not None:
        raise ImportError_("Dieser Importlauf wurde bereits rückgängig gemacht")
    links = list(db.scalars(select(ImportLink).where(ImportLink.created_run == run_id).order_by(ImportLink.id.desc())))
    removed: Counter = Counter()
    by_kind: dict[str, list[ImportLink]] = defaultdict(list)
    for ln in links:
        by_kind[ln.target_kind].append(ln)

    def ids(kind: str) -> list[int]:
        out = []
        for ln in by_kind.get(kind, []):
            try:
                out.append(int(ln.target_id))
            except ValueError:
                continue
        return out

    students = [ln.target_id for ln in by_kind.get("student_created", [])]
    teachers = [ln.target_id for ln in by_kind.get("teacher_created", [])]
    classes = [ln.target_id for ln in by_kind.get("class_created", [])]
    if students or teachers or classes:
        def drop(sc: School) -> None:
            sc.students = [s for s in sc.students if s.id not in students]
            sc.teachers = [t for t in sc.teachers if t.id not in teachers]
            used = {s.class_id for s in sc.students}
            sc.classes = [c for c in sc.classes if c.id not in classes or c.id in used]
        get_store().mutate(user, f"Import #{run_id} rückgängig", drop, scope=["students", "teachers", "classes", "import"])
        removed["student"], removed["teacher"], removed["class"] = len(students), len(teachers), len(classes)
    for sid in ids("submission"):
        db.execute(delete(AssignmentSubmission).where(AssignmentSubmission.id == sid))
        removed["submission"] += 1
    for ln in by_kind.get("gradesource", []):
        gs.withdraw_results(db, "moodle", ln.target_id)
        removed["gradesource"] += 1
    for iid in ids("item"):
        at.withdraw_from_gradebook(db, iid)
        db.execute(delete(ChannelItem).where(ChannelItem.id == iid), execution_options={"include_trashed": True})
        removed["item"] += 1
    for tid in ids("selftest"):
        db.execute(delete(LearningSelftest).where(LearningSelftest.id == tid))
        removed["selftest"] += 1
    for qid in ids("question"):
        db.execute(delete(LearningQuestion).where(LearningQuestion.id == qid))
        removed["question"] += 1
    for pid in ids("post"):
        db.execute(delete(ChannelPost).where(ChannelPost.id == pid))
        removed["post"] += 1
    for gid in ids("group"):
        grp = db.get(ChannelGroup, gid)
        if grp is not None:
            db.execute(delete(ChannelGroupMember).where(ChannelGroupMember.group_id == gid))
            db.delete(grp)
            removed["group"] += 1
    for fid in ids("folder"):
        db.execute(delete(ChannelFolder).where(ChannelFolder.id == fid), execution_options={"include_trashed": True})
        removed["folder"] += 1
    for ln in by_kind.get("member", []):
        chid, _, uid = ln.target_id.partition(":")
        db.execute(delete(ChannelExtraMember).where(ChannelExtraMember.channel_id == int(chid),
                                                    ChannelExtraMember.user_id == int(uid)))
        removed["member"] += 1
    for aid in ids("assessment"):
        db.execute(delete(CompAssessment).where(CompAssessment.id == aid))
        removed["assessment"] += 1
    for ln in by_kind.get("award", []):
        bid, _, sid = ln.target_id.partition(":")
        db.execute(delete(CompBadgeAward).where(CompBadgeAward.badge_id == int(bid), CompBadgeAward.student_id == sid))
        removed["award"] += 1
    for bid in ids("badge"):
        db.execute(delete(CompBadge).where(CompBadge.id == bid))
        removed["badge"] += 1
    for fid in ids("framework"):
        db.execute(delete(CompFramework).where(CompFramework.id == fid))
        removed["framework"] += 1
    for cid in ids("channel"):
        db.execute(delete(Channel).where(Channel.id == cid, Channel.kind == "custom"))
        removed["channel"] += 1
    for ln in links:
        db.delete(ln)
    run.status, run.undone_at = "zurueckgenommen", utcnow()
    run.undone_by = (getattr(user, "username", "") or "")[:80]
    audit(db, user, "import.fremd.undo", f"run:{run_id}", {"removed": dict(removed)})
    db.flush()
    return {"run_id": run_id, "removed": dict(removed),
            "hint": "Geänderte (nicht neu angelegte) Daten wurden nicht zurückgesetzt."}
