"""Importe aus Fremdsystemen: Kursräume, Aufgaben, Selbsttests, Notenbuch-Quellen, Kompetenzen, Abzeichen, Forum.

Teil von :class:`schulmanager.server.import_fremd.Importer` (Mixin, getrennt wegen der Dateigröße). Jeder Kurs läuft in
einem Savepoint: scheitert etwas, wird nur dieser Kurs zurückgerollt und gemeldet.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any, Optional

from sqlalchemy import select

from .. import competency as comp_logic
from .. import grading, learning
from ..integrations.fremd.model import FAssign, FCourse, FFramework, FGradeItem, FQuiz
from . import assignment_tools as at
from . import competency_db, files, gradebook_sources as gs, learning_service as ls
from .db import utcnow
from .feature_models.channel_groups import ChannelGroup, ChannelGroupMember, ChannelGroupSet
from .feature_models.channels import (AssignmentSubmission, Channel, ChannelExtraMember, ChannelFolder, ChannelItem,
                                      ChannelPost)
from .feature_models.competency import CompAssessment, CompBadge, CompBadgeAward, CompCompetency
from .feature_models.learning import LearningQuestion, LearningSelftest

log = logging.getLogger("schulmanager.import_fremd")
GERMAN_GRADE_WORDS = {"sehr gut": "1", "gut": "2", "befriedigend": "3", "ausreichend": "4", "mangelhaft": "5",
                      "ungenügend": "6", "ungenuegend": "6"}
gs.set_label("moodle", "Import (Moodle)")


def _fp(*parts: Any) -> str:
    import hashlib
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


class RoomsMixin:
    # Attribute des Importers (für Typprüfer/Leser)
    db: Any
    user: Any
    b: Any
    o: Any
    dry: bool
    run: Any
    system: str
    cnt: dict
    waiting: Counter

    # ------------------------------------------------------------------ Kurse
    def apply_courses(self) -> None:
        for src, info in self.course_target.items():            # type: ignore[attr-defined]
            if info["mode"] == "skip":
                self.count("course", "skipped")                 # type: ignore[attr-defined]
                continue
            course = self.b.courses[src]
            snap = {k: Counter(v) for k, v in self.cnt.items()}
            mark = len(self._link_log)                          # type: ignore[attr-defined]
            sp = self.db.begin_nested()
            try:
                self._apply_course(course, info)
                sp.commit()
            except Exception as exc:  # noqa: BLE001 - ein Kurs darf den Lauf nie stoppen
                sp.rollback()
                log.exception("Import: Kurs %s", src)
                for key in self._link_log[mark:]:               # type: ignore[attr-defined]
                    self.links.pop(key, None)                   # type: ignore[attr-defined]
                del self._link_log[mark:]                       # type: ignore[attr-defined]
                self.cnt.clear()
                self.cnt.update(snap)
                self.problem("fehler", f"course:{src}", f"Kurs „{course.title}“ nicht importiert: {str(exc)[:200]}")  # type: ignore[attr-defined]

    def _apply_course(self, course: FCourse, info: dict) -> None:
        o = self.o
        ch, our = self._channel(course, info)
        self.folders: dict[int, ChannelFolder] = {}
        self.group_ids: dict[str, int] = {}
        self.group_set_of: dict[str, int] = {}
        if o.parts and "kursraeume" in o.parts and ch.kind == "custom":
            self._members(ch, course)
        if "gruppen" in o.parts:
            self._groups(ch, course)
        if "aufgaben" in o.parts:
            for a in (x for x in self.b.assigns if x.course == course.src_id):
                self._assign(ch, course, a, our)
        if "fragen" in o.parts:
            for z in (x for x in self.b.quizzes if x.course == course.src_id):
                self._quiz(ch, course, z)
        if "noten" in o.parts:
            for gi in (x for x in self.b.grade_items if x.course == course.src_id):
                self._grade_item(course, gi, our)
        if "dateien" in o.parts:
            self._files(ch, course)
        if "forum" in o.parts:
            self._posts(ch, course)

    def _channel(self, course: FCourse, info: dict) -> tuple[Channel, Optional[tuple[str, int]]]:
        db = self.db
        lk = self.link("course", course.src_id)              # type: ignore[attr-defined]
        if info["mode"] == "linked" and lk is not None and lk.target_kind == "channel_course":
            info = {**info, "mode": "mapped", "ref": lk.target_id}
        if info["mode"] == "mapped":
            ref = info["ref"]
            cid, _, part = ref.rpartition("#")
            ch = db.scalar(select(Channel).where(Channel.kind == "course", Channel.ref == ref))
            if ch is None:
                ch = Channel(kind="course", ref=ref, title=course.title[:200], description="", settings=None,
                             archived=False, created_at=utcnow())
                db.add(ch)
                db.flush()
            self.put_link("course", course.src_id, "channel_course", ref, _fp(ref))        # type: ignore[attr-defined]
            self.count("course", "unchanged" if lk else "created")                           # type: ignore[attr-defined]
            return ch, (cid, int(part))
        ch = None
        if lk is not None and lk.target_kind == "channel":
            ch = db.get(Channel, int(lk.target_id))
        fp = _fp(course.title, course.summary, course.hidden)
        if ch is None:
            if lk is not None:
                self.notes.append(f"Kursraum zu „{course.title}“ wurde inzwischen gelöscht – neu angelegt")  # type: ignore[attr-defined]
            ch = Channel(kind="custom", ref=None, title=course.title[:200], description=course.summary[:2000],
                         settings={"students_can_post": True, "students_can_reply": True}, archived=course.hidden,
                         created_by=getattr(self.user, "id", None) or None, created_at=utcnow())
            db.add(ch)
            db.flush()
            self.put_link("course", course.src_id, "channel", ch.id, fp)                      # type: ignore[attr-defined]
            self.count("course", "created")                                                    # type: ignore[attr-defined]
        elif lk is not None and lk.fingerprint != fp:
            ch.title, ch.description, ch.archived = course.title[:200], course.summary[:2000], course.hidden
            ch.updated_at = utcnow()
            self.put_link("course", course.src_id, "channel", ch.id, fp)                      # type: ignore[attr-defined]
            self.count("course", "updated")                                                    # type: ignore[attr-defined]
        else:
            self.count("course", "unchanged")                                                  # type: ignore[attr-defined]
        return ch, None

    # ------------------------------------------------------------------ Mitglieder (eigene Kursräume)
    def _members(self, ch: Channel, course: FCourse) -> None:
        db = self.db
        have = {uid: r for uid, r in db.execute(select(ChannelExtraMember.user_id, ChannelExtraMember.role)
                                                .where(ChannelExtraMember.channel_id == ch.id))}
        teacher_present = any(r == "teacher" for r in have.values())
        for e in (x for x in self.b.enrols if x.course == course.src_id):
            if not e.active:
                self.count("member", "skipped")                                                # type: ignore[attr-defined]
                continue
            uid = self.user_of(e.person)                                                       # type: ignore[attr-defined]
            if uid is None:
                self.waiting["members"] += 1
                continue
            if uid in have:
                self.count("member", "unchanged")                                              # type: ignore[attr-defined]
                continue
            role = "student" if e.role == "student" else "teacher"
            db.add(ChannelExtraMember(channel_id=ch.id, user_id=uid, role=role,
                                      added_by=getattr(self.user, "id", None) or None, created_at=utcnow()))
            have[uid] = role
            teacher_present = teacher_present or role == "teacher"
            self.put_link("member", f"{course.src_id}:{e.person}", "member", f"{ch.id}:{uid}")  # type: ignore[attr-defined]
            self.count("member", "created")                                                    # type: ignore[attr-defined]
        uid_importer = getattr(self.user, "id", None)
        if not teacher_present and uid_importer and uid_importer not in have:
            db.add(ChannelExtraMember(channel_id=ch.id, user_id=uid_importer, role="teacher", added_by=uid_importer,
                                      created_at=utcnow()))
            self.notes.append(f"„{course.title}“: keine Lehrkraft mit Konto gefunden – Sie sind als Lehrende/r eingetragen")  # type: ignore[attr-defined]
        db.flush()

    # ------------------------------------------------------------------ Gruppen
    def _groups(self, ch: Channel, course: FCourse) -> None:
        db = self.db
        groups = [g for g in self.b.groups if g.course == course.src_id]
        if not groups:
            return
        sets: dict[str, ChannelGroupSet] = {}
        for g in groups:
            lk = self.link("group", g.src_id)                                                  # type: ignore[attr-defined]
            row = db.get(ChannelGroup, int(lk.target_id)) if lk else None
            if row is None:
                name = (g.grouping or "Gruppen aus dem Import")[:120]
                gs_ = sets.get(name)
                if gs_ is None:
                    gs_ = db.scalar(select(ChannelGroupSet).where(ChannelGroupSet.channel_id == ch.id,
                                                                  ChannelGroupSet.name == name))
                if gs_ is None:
                    gs_ = ChannelGroupSet(channel_id=ch.id, name=name,
                                          created_by=getattr(self.user, "id", None) or None)
                    db.add(gs_)
                    db.flush()
                sets[name] = gs_
                row = ChannelGroup(channel_id=ch.id, set_id=gs_.id, name=g.name[:120], position=len(sets))
                db.add(row)
                db.flush()
                self.put_link("group", g.src_id, "group", row.id)                              # type: ignore[attr-defined]
                self.count("group", "created")                                                 # type: ignore[attr-defined]
            else:
                self.count("group", "unchanged")                                               # type: ignore[attr-defined]
            self.group_ids[g.src_id] = row.id
            self.group_set_of[g.src_id] = row.set_id
            taken = {uid for (uid,) in db.execute(select(ChannelGroupMember.user_id).where(
                ChannelGroupMember.set_id == row.set_id))}
            for m in g.members:
                uid = self.user_of(m)                                                          # type: ignore[attr-defined]
                if uid is None:
                    self.waiting["group_members"] += 1
                    continue
                if uid in taken:
                    continue
                db.add(ChannelGroupMember(channel_id=ch.id, set_id=row.set_id, group_id=row.id, user_id=uid))
                taken.add(uid)
                self.count("group_member", "created")                                          # type: ignore[attr-defined]
        db.flush()

    # ------------------------------------------------------------------ Ordner
    def _folder(self, ch: Channel, course: FCourse, section: int) -> Optional[int]:
        if not section:
            return None
        f = self.folders.get(section)
        if f is not None:
            return f.id
        lk = self.link("folder", f"{course.src_id}:{section}")                                  # type: ignore[attr-defined]
        f = self.db.get(ChannelFolder, int(lk.target_id)) if lk else None
        if f is None:
            name = (course.sections.get(section) or f"Abschnitt {section}")[:120]
            f = ChannelFolder(channel_id=ch.id, parent_id=None, name=name, position=section, hidden=False,
                              created_by=getattr(self.user, "id", None) or None, created_at=utcnow())
            self.db.add(f)
            self.db.flush()
            self.put_link("folder", f"{course.src_id}:{section}", "folder", f.id)               # type: ignore[attr-defined]
            self.count("folder", "created")                                                     # type: ignore[attr-defined]
        self.folders[section] = f
        return f.id

    # ------------------------------------------------------------------ Aufgaben
    def _assign(self, ch: Channel, course: FCourse, a: FAssign, our: Optional[tuple[str, int]]) -> None:
        db = self.db
        visible = self.o.publish and a.visible
        fp = _fp(a.title, a.intro, a.due, a.cutoff, a.max_points, a.team, a.rubric, a.section, a.visible)
        lk = self.link("assign", a.src_id)                                                      # type: ignore[attr-defined]
        item = db.get(ChannelItem, int(lk.target_id)) if lk else None
        if lk is not None and item is None:
            self.notes.append(f"Aufgabe „{a.title}“ wurde im Kursraum gelöscht – nicht erneut angelegt")  # type: ignore[attr-defined]
            self.count("assign", "skipped")                                                     # type: ignore[attr-defined]
            return
        late_ok = a.cutoff is None or (a.due is not None and a.cutoff > a.due)
        if item is None:
            item = ChannelItem(channel_id=ch.id, folder_id=self._folder(ch, course, a.section), type="assignment",
                               title=a.title[:200], body_enc="", visibility="visible" if visible else "hidden",
                               due_at=a.due, allow_late=late_ok or a.cutoff is None, position=0, submittable=True,
                               created_by=getattr(self.user, "id", None) or None, created_at=utcnow())
            db.add(item)
            db.flush()
            item.write_text("body", a.intro)
            self.put_link("assign", a.src_id, "item", item.id, fp)                              # type: ignore[attr-defined]
            self.count("assign", "created")                                                     # type: ignore[attr-defined]
            changed = True
        elif lk.fingerprint != fp:                                                              # type: ignore[union-attr]
            item.title, item.due_at, item.allow_late = a.title[:200], a.due, late_ok or a.cutoff is None
            item.write_text("body", a.intro)
            item.updated_at = utcnow()
            self.put_link("assign", a.src_id, "item", item.id, fp)                              # type: ignore[attr-defined]
            self.count("assign", "updated")                                                     # type: ignore[attr-defined]
            changed = True
        else:
            self.count("assign", "unchanged")                                                   # type: ignore[attr-defined]
            changed = False
        st = at.get_or_create_settings(db, item.id)
        if changed:
            if a.rubric:
                st.set_rubric(a.rubric)
                st.rubric_title = a.title[:200]
            else:
                st.max_points = a.max_points
            first_group = next((s.group for s in a.submissions if s.group), "")
            if a.team and first_group in self.group_set_of:
                st.group_mode, st.group_set_id = True, self.group_set_of[first_group]
            st.updated_at = utcnow()
        if a.team and not st.group_mode:
            self.notes.append(f"Aufgabe „{a.title}“ ist eine Gruppenabgabe, die Gruppen konnten nicht zugeordnet werden")  # type: ignore[attr-defined]
        for s in a.submissions:
            self._submission(item, a, s, st)
        db.flush()
        if our is not None:
            at.publish_to_gradebook(db, item)

    def _submission(self, item: ChannelItem, a: FAssign, s, st) -> None:
        db = self.db
        uid = self.user_of(s.person)                                                            # type: ignore[attr-defined]
        if uid is None:
            self.waiting["submissions"] += 1
            return
        key = f"{a.src_id}:{s.person}"
        fp = _fp(s.text, s.at, s.points, s.max_points, s.feedback, s.status, s.rubric_fill, [f.name for f in s.files],
                 s.group)
        lk = self.link("submission", key)                                                       # type: ignore[attr-defined]
        row = db.scalar(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id,
                                                           AssignmentSubmission.student_user_id == uid))
        if row is not None and lk is None:
            self.count("submission", "skipped")                                                 # type: ignore[attr-defined]
            self.problem("konflikt", f"submission:{key}", "Abgabe existiert bereits im Kursraum – nicht überschrieben")  # type: ignore[attr-defined]
            return
        if row is not None and lk is not None and lk.fingerprint == fp:
            self.count("submission", "unchanged")                                               # type: ignore[attr-defined]
            return
        text = s.text
        if s.files:
            names = ", ".join(f.name for f in s.files)
            text = (text + "\n\n" if text else "") + f"_Dateien in der Quelle (Inhalt nicht übernommen): {names}_"
        points, top, grade, fill = s.points, s.max_points, "", None
        if a.rubric and s.rubric_fill:
            try:
                points, fill, _complete = grading.score_fill(a.rubric, s.rubric_fill)
                top = grading.max_points(a.rubric)
            except ValueError as exc:
                self.problem("zeile", f"submission:{key}", f"Raster-Bewertung nicht lesbar: {exc}")  # type: ignore[attr-defined]
                fill, points = None, s.points
        if s.status == "bewertet" and points is not None:
            grade = grading.grade_for(points, top, dict(grading.DEFAULT_SCALE)) or ""
        status = {"bewertet": "bewertet", "verspätet": "verspaetet"}.get(s.status, "abgegeben")
        created = row is None
        if row is None:
            row = AssignmentSubmission(item_id=item.id, student_user_id=uid, student_id=self.student_of(s.person),   # type: ignore[attr-defined]
                                       text_enc="", feedback_enc="", grade_enc="", rubric_enc="", attempt=1,
                                       status=status, created_at=utcnow())
            db.add(row)
            db.flush()
        row.status, row.submitted_at = status, s.at
        row.group_id = self.group_ids.get(s.group) if s.group else None
        row.write_text("text", text)
        row.write_text("feedback", s.feedback)
        row.write_text("grade", grade)
        row.write_text("rubric", json.dumps(fill, ensure_ascii=False) if fill else "")
        row.points = points if s.status == "bewertet" else None
        row.max_points = top if s.status == "bewertet" and points is not None else None
        row.feedback_at = s.graded_at if s.status == "bewertet" else None
        row.updated_at = utcnow()
        self.put_link("submission", key, "submission", row.id, fp)                              # type: ignore[attr-defined]
        self.count("submission", "created" if created else "updated")                           # type: ignore[attr-defined]

    # ------------------------------------------------------------------ Selbsttests
    def _quiz(self, ch: Channel, course: FCourse, z: FQuiz) -> None:
        db = self.db
        ids: list[int] = []
        for entry in z.questions:
            q = self.b.questions.get(entry)
            if q is None:
                continue
            key = f"{course.src_id}:{entry}"
            if q.data is None:
                self.count("question", "skipped")                                               # type: ignore[attr-defined]
                self.problem("nicht_unterstuetzt", f"question:{key}", f"Frage „{q.title}“: {q.reason}")  # type: ignore[attr-defined]
                continue
            try:
                norm = learning.normalize_question(q.data)
            except learning.LearningError as exc:
                self.count("question", "skipped")                                               # type: ignore[attr-defined]
                self.problem("zeile", f"question:{key}", f"Frage „{q.title}“ nicht übernehmbar: {exc}")  # type: ignore[attr-defined]
                continue
            fp = _fp(norm)
            lk = self.link("question", key)                                                     # type: ignore[attr-defined]
            row = db.get(LearningQuestion, int(lk.target_id)) if lk else None
            if row is None:
                row = LearningQuestion(channel_id=ch.id, qtype=norm["type"], category=(norm.get("category") or "")[:60],
                                       data_enc="", created_by=getattr(self.user, "id", None) or None,
                                       created_at=utcnow())
                db.add(row)
                db.flush()
                ls.write_json(row, "data", norm)
                self.put_link("question", key, "question", row.id, fp)                          # type: ignore[attr-defined]
                self.count("question", "created")                                               # type: ignore[attr-defined]
            elif lk.fingerprint != fp:                                                          # type: ignore[union-attr]
                row.qtype = norm["type"]
                ls.write_json(row, "data", norm)
                row.updated_at = utcnow()
                self.put_link("question", key, "question", row.id, fp)                          # type: ignore[attr-defined]
                self.count("question", "updated")                                               # type: ignore[attr-defined]
            else:
                self.count("question", "unchanged")                                             # type: ignore[attr-defined]
            ids.append(row.id)
        if not ids:
            self.count("selftest", "skipped")                                                   # type: ignore[attr-defined]
            self.problem("nicht_unterstuetzt", f"quiz:{z.src_id}", f"Test „{z.title}“ ohne übernehmbare Fragen")  # type: ignore[attr-defined]
            return
        fp = _fp(z.title, z.intro, ids, z.time_limit_min, z.max_attempts, z.opens, z.closes)
        lk = self.link("quiz", z.src_id)                                                        # type: ignore[attr-defined]
        test = db.get(LearningSelftest, int(lk.target_id)) if lk else None
        status = "offen" if (self.o.publish and z.visible) else "entwurf"
        if test is None:
            test = LearningSelftest(channel_id=ch.id, title=z.title[:200], description_enc="", status=status,
                                    question_ids=ids, max_attempts=z.max_attempts, time_limit_min=z.time_limit_min,
                                    shuffle_questions=False, shuffle_answers=True, immediate_feedback=False,
                                    review="full", opens_at=z.opens, closes_at=z.closes,
                                    created_by=getattr(self.user, "id", None) or None, created_at=utcnow())
            db.add(test)
            db.flush()
            test.write_text("description", z.intro)
            self.put_link("quiz", z.src_id, "selftest", test.id, fp)                            # type: ignore[attr-defined]
            self.count("selftest", "created")                                                   # type: ignore[attr-defined]
        elif lk.fingerprint != fp:                                                              # type: ignore[union-attr]
            test.title, test.question_ids = z.title[:200], ids
            test.max_attempts, test.time_limit_min = z.max_attempts, z.time_limit_min
            test.opens_at, test.closes_at = z.opens, z.closes
            test.write_text("description", z.intro)
            test.updated_at = utcnow()
            self.put_link("quiz", z.src_id, "selftest", test.id, fp)                            # type: ignore[attr-defined]
            self.count("selftest", "updated")                                                   # type: ignore[attr-defined]
        else:
            self.count("selftest", "unchanged")                                                 # type: ignore[attr-defined]

    # ------------------------------------------------------------------ Notenbuch-Quellen
    def _grade_item(self, course: FCourse, gi: FGradeItem, our: Optional[tuple[str, int]]) -> None:
        if gi.kind == "assign":
            return                                                                              # läuft über die Aufgabe selbst
        if our is None:
            self.count("grade_item", "skipped")                                                 # type: ignore[attr-defined]
            self.notes.append(f"Bewertung „{gi.title}“ ({course.title}): Notenbuch gibt es nur für zugeordnete Kurse")  # type: ignore[attr-defined]
            return
        results = []
        for pid, (pts, text) in gi.results.items():
            sid = self.student_of(pid)                                                          # type: ignore[attr-defined]
            if sid is None:
                self.waiting["grades"] += 1
                continue
            if pts is not None:
                results.append(gs.SourceResult(sid, points=round(pts, 4)))
            elif text:
                results.append(gs.SourceResult(sid, grade=GERMAN_GRADE_WORDS.get(text.strip().lower(), text.strip())))
        sid_ = f"{self.o.instance}:{gi.src_id}"[:80]
        fp = _fp(gi.title, gi.max_points, gi.date, [(r.student_id, r.points, r.grade) for r in results])
        lk = self.link("gradeitem", gi.src_id)                                                  # type: ignore[attr-defined]
        if lk is not None and lk.fingerprint == fp:
            self.count("grade_item", "unchanged")                                               # type: ignore[attr-defined]
            return
        gs.publish_results(self.db, source_type="moodle", source_id=sid_, course_id=our[0], part=our[1],
                           title=gi.title, date=gi.date, max_points=gi.max_points if gi.kind != "scale" else None,
                           results=results)
        self.put_link("gradeitem", gi.src_id, "gradesource", sid_, fp)                          # type: ignore[attr-defined]
        self.count("grade_item", "updated" if lk else "created")                                # type: ignore[attr-defined]

    # ------------------------------------------------------------------ Dateien (Platzhalter bzw. Inhalt)
    def _files(self, ch: Channel, course: FCourse) -> None:
        db = self.db
        todo = [f for f in self.b.files if f.course == course.src_id]
        if not todo:
            return
        folder: Optional[int] = None
        for f in todo:
            lk = self.link("file", f.src_id)                                                    # type: ignore[attr-defined]
            if lk is not None:
                self.count("file", "unchanged")                                                 # type: ignore[attr-defined]
                continue
            if folder is None:
                key = f"{course.src_id}:files"
                flk = self.link("folder", key)                                                  # type: ignore[attr-defined]
                fo = db.get(ChannelFolder, int(flk.target_id)) if flk else None
                if fo is None:
                    fo = ChannelFolder(channel_id=ch.id, parent_id=None, name="Dateien aus dem Import", position=999,
                                       hidden=False, created_at=utcnow(),
                                       created_by=getattr(self.user, "id", None) or None)
                    db.add(fo)
                    db.flush()
                    self.put_link("folder", key, "folder", fo.id)                               # type: ignore[attr-defined]
                folder = fo.id
            size = f"{f.size / 1024:.0f} KB" if f.size else "Größe unbekannt"
            item = ChannelItem(channel_id=ch.id, folder_id=folder, type="text", title=f.name[:200], body_enc="",
                               visibility="visible" if self.o.publish else "hidden", position=0,
                               created_by=getattr(self.user, "id", None) or None, created_at=utcnow())
            if f.data is not None and not self.dry:
                try:
                    meta = files.store_bytes(db, None, f.data, f.name, f.mime or None, purpose="channel_material")
                    item.type, item.file_id = "file", meta.id
                except Exception as exc:  # noqa: BLE001 - Dateityp/Größe nicht erlaubt → Platzhalter
                    self.problem("nicht_unterstuetzt", f"file:{f.src_id}", f"{f.name}: {getattr(exc, 'detail', exc)}")  # type: ignore[attr-defined]
            db.add(item)
            db.flush()
            if item.type == "file" and item.file_id:
                files.attach(db, item.file_id, None, "channel_item", item.id)
            else:
                item.write_text("body", f"Datei „{f.name}“ ({f.mime or 'Typ unbekannt'}, {size}) – "
                                        "der Inhalt wurde beim Import nicht übernommen.")
            self.put_link("file", f.src_id, "item", item.id)                                    # type: ignore[attr-defined]
            self.count("file", "created")                                                       # type: ignore[attr-defined]

    # ------------------------------------------------------------------ Forum → Pinnwand
    def _posts(self, ch: Channel, course: FCourse) -> None:
        db = self.db
        mapping: dict[str, int] = {}
        for p in (x for x in self.b.posts if x.course == course.src_id):
            lk = self.link("post", p.src_id)                                                    # type: ignore[attr-defined]
            if lk is not None:
                mapping[p.src_id] = int(lk.target_id)
                self.count("post", "unchanged")                                                 # type: ignore[attr-defined]
                continue
            parent = mapping.get(p.parent)
            if p.parent and parent is None:
                parent_row = db.get(ChannelPost, mapping.get(p.parent, 0)) if mapping.get(p.parent) else None
                parent = parent_row.id if parent_row else None
            if parent is not None:
                root = db.get(ChannelPost, parent)
                if root is not None and root.parent_id:
                    parent = root.parent_id                   # nur eine Antwortebene
            body = p.body
            if not p.parent and p.subject:
                body = f"**{p.subject}**\n\n{body}" if body else f"**{p.subject}**"
            row = ChannelPost(channel_id=ch.id, parent_id=parent, author_id=None, author_name=p.author[:200],
                              body_enc="", pinned=False, created_at=p.at or utcnow())
            db.add(row)
            db.flush()
            row.write_text("body", body)
            mapping[p.src_id] = row.id
            self.put_link("post", p.src_id, "post", row.id)                                     # type: ignore[attr-defined]
            self.count("post", "created")                                                       # type: ignore[attr-defined]

    # ------------------------------------------------------------------ Kompetenzen
    def apply_frameworks(self) -> None:
        for fw in self.b.frameworks:
            sp = self.db.begin_nested()
            mark = len(self._link_log)                                                          # type: ignore[attr-defined]
            try:
                self._framework(fw)
                sp.commit()
            except Exception as exc:  # noqa: BLE001
                sp.rollback()
                for key in self._link_log[mark:]:                                               # type: ignore[attr-defined]
                    self.links.pop(key, None)                                                   # type: ignore[attr-defined]
                del self._link_log[mark:]                                                       # type: ignore[attr-defined]
                self.problem("fehler", f"framework:{fw.src_id}", f"Kompetenzrahmen „{fw.name}“: {str(exc)[:200]}")  # type: ignore[attr-defined]

    def _framework(self, fw: FFramework) -> None:
        db = self.db
        lk = self.link("framework", fw.src_id)                                                  # type: ignore[attr-defined]
        comp_by_src: dict[str, int] = {}
        if lk is not None and db.get(competency_db.CompFramework, int(lk.target_id)) is not None:
            self.count("framework", "unchanged")                                                # type: ignore[attr-defined]
            for (k, src), row in list(self.links.items()):                                      # type: ignore[attr-defined]
                if k == "competency":
                    comp_by_src[src] = int(row.target_id)
        else:
            template = comp_logic.normalize_template({
                "name": fw.name, "subject": "", "description": fw.description, "levels": fw.levels,
                "support_level": min(fw.support_level, len(fw.levels) - 1),
                "areas": [{"name": a["name"], "competencies": [
                    {"code": c.get("code", ""), "title": c["title"], "descriptors": c.get("descriptors", [])}
                    for c in a["competencies"]]} for a in fw.areas if a["competencies"]]})
            row = competency_db.create_framework(db, template, self.user)
            order = [c["src_id"] for a in fw.areas if a["competencies"] for c in a["competencies"]]
            ids = [cid for (cid,) in db.execute(select(CompCompetency.id).where(
                CompCompetency.framework_id == row.id).order_by(CompCompetency.area_id, CompCompetency.position))]
            for src, cid in zip(order, ids):
                comp_by_src[src] = cid
                self.put_link("competency", src, "competency", cid)                              # type: ignore[attr-defined]
            self.put_link("framework", fw.src_id, "framework", row.id)                           # type: ignore[attr-defined]
            self.count("framework", "created")                                                   # type: ignore[attr-defined]
        levels = len(fw.levels)
        for pid, csrc, level, day, note in fw.assessments:
            sid = self.student_of(pid)                                                           # type: ignore[attr-defined]
            cid = comp_by_src.get(csrc)
            if sid is None or cid is None:
                self.waiting["assessments"] += 1 if sid is None else 0
                continue
            key = f"{pid}:{csrc}:{day}:{level}"
            if self.link("assessment", key) is not None:                                         # type: ignore[attr-defined]
                self.count("assessment", "unchanged")                                            # type: ignore[attr-defined]
                continue
            row = CompAssessment(student_id=sid, competency_id=cid, kind="teacher", level=max(1, min(level, levels)),
                                 assessed_on=day or utcnow().date().isoformat(), evidence_type="note" if note else "",
                                 evidence_ref="", evidence_enc="", comment_enc="", by_user_id=None,
                                 by_name="Import", created_at=utcnow())
            db.add(row)
            db.flush()
            if note:
                from . import crypto
                row.comment_enc = crypto.encrypt_text(note[:1000], row.aad("comment"))
            self.put_link("assessment", key, "assessment", row.id)                               # type: ignore[attr-defined]
            self.count("assessment", "created")                                                  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ Abzeichen
    def apply_badges(self) -> None:
        db = self.db
        for bd in self.b.badges:
            lk = self.link("badge", bd.src_id)                                                   # type: ignore[attr-defined]
            row = db.get(CompBadge, int(lk.target_id)) if lk else None
            if row is None:
                row = CompBadge(name=bd.name[:100], description=bd.description[:300], icon="medal", color="gold",
                                criteria=None, active=bd.active, created_by=getattr(self.user, "id", None) or None,
                                created_at=utcnow())
                db.add(row)
                db.flush()
                self.put_link("badge", bd.src_id, "badge", row.id)                               # type: ignore[attr-defined]
                self.count("badge", "created")                                                   # type: ignore[attr-defined]
            else:
                self.count("badge", "unchanged")                                                 # type: ignore[attr-defined]
            have = {sid for (sid,) in db.execute(select(CompBadgeAward.student_id).where(CompBadgeAward.badge_id == row.id))}
            for pid, day in bd.awards:
                sid = self.student_of(pid)                                                       # type: ignore[attr-defined]
                if sid is None:
                    self.waiting["awards"] += 1 if self.person_target.get(pid) is None else 0     # type: ignore[attr-defined]
                    continue
                if sid in have:
                    continue
                db.add(CompBadgeAward(badge_id=row.id, student_id=sid, awarded_on=day or utcnow().date().isoformat(),
                                      awarded_by=None, awarded_by_name="Import", auto=False, note_enc=""))
                have.add(sid)
                self.put_link("award", f"{bd.src_id}:{pid}", "award", f"{row.id}:{sid}")         # type: ignore[attr-defined]
                self.count("award", "created")                                                   # type: ignore[attr-defined]
        db.flush()
