"""Kompetenzraster: Datenbankzugriff, Sichtregeln und Aufbereitung (Routen: ``routes/features_competency*.py``).

Sichtstufen auf die Daten einer Schülerin/eines Schülers (:class:`Access.view_kind`):

* ``staff``  – Lehrkraft/Leitung mit ``competency.read`` im Umfang (alles, auch Beobachtungsnotizen)
* ``self``   – die Schülerin/der Schüler selbst
* ``family`` – Eltern (volljährige Kinder nur mit Freigabe im Bereich ``kompetenzen``)

Schüler/innen und Eltern sehen keine Beobachtungsnotizen (``evidence_type == "note"``) und keine Markierung
„braucht Unterstützung“.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from schulmanager import competency as logic
from schulmanager.server import crypto
from schulmanager.server import parent_access as pa
from schulmanager.server.db import iso, utcnow
from schulmanager.server.feature_models.competency import (
    CompArea,
    CompAssessment,
    CompBadge,
    CompBadgeAward,
    CompCompetency,
    CompFramework,
    CompLink,
    CompPlan,
)

from .routes.features_common import has, index, own_student_ids, snapshot, students_in_scope

ITEM_TYPE_RE = re.compile(r"^[a-z][a-z_]{0,29}$")
ITEM_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,60}$")
REF_RE = re.compile(r"^[a-z][a-z_]{0,29}:[A-Za-z0-9_.-]{1,60}$")


def dec(token: str, aad: str) -> str:
    if not token:
        return ""
    try:
        return crypto.decrypt_text(token, aad)
    except Exception:  # noqa: BLE001
        return ""


def today() -> date:
    return date.today()


# --------------------------------------------------------------------------------------------------- Zugriff
class Access:
    """Wer darf welche Schülerin/welchen Schüler lesen bzw. bewerten."""

    def __init__(self, user: Any, db: Session, snap: Any = None) -> None:
        self.user, self.db = user, db
        self.snap = snap or snapshot()
        self.school = self.snap[1]
        self.role = getattr(user, "role", "")
        self._read: Any = False
        self._assess: Any = False

    def students(self) -> dict:
        return index("students", self.snap)

    def student(self, sid: str):
        return self.students().get(sid)

    def read_scope(self) -> Optional[frozenset[str]]:
        if self._read is False:
            self._read = students_in_scope(self.user, "competency.read", self.snap)
        return self._read

    def assess_scope(self) -> Optional[frozenset[str]]:
        if self._assess is False:
            self._assess = students_in_scope(self.user, "competency.assess", self.snap)
        return self._assess

    def can_assess(self, sid: str) -> bool:
        if not has(self.user, "competency.assess") or self.student(sid) is None:
            return False
        scope = self.assess_scope()
        return scope is None or sid in scope

    def view_kind(self, sid: str) -> Optional[str]:
        """``staff`` | ``self`` | ``family`` | ``None`` (kein Zugriff → 404)."""
        if self.student(sid) is None:
            return None
        if self.role in ("schueler", "eltern"):
            if sid not in own_student_ids(self.user):
                return None
            if self.role == "schueler":
                return "self"
            return "family" if pa.parent_may_see(self.db, sid, pa.AREA_COMPETENCIES, school=self.school) else None
        if has(self.user, "competency.read"):
            scope = self.read_scope()
            if scope is None or sid in scope:
                return "staff"
        return None

    def visible_students(self) -> Optional[frozenset[str]]:
        """Alle Schüler/innen, die das Konto im Lehrer-Sinn lesen darf (``None`` = alle)."""
        return self.read_scope() if has(self.user, "competency.read") else frozenset()


# ------------------------------------------------------------------------------------------------ Rahmen
def tree(db: Session, framework_ids: Optional[Iterable[int]] = None, *, archived: bool = False) -> list[dict]:
    """Rahmen mit Bereichen und Kompetenzen (nach Position)."""
    q = select(CompFramework).order_by(CompFramework.name, CompFramework.id)
    if framework_ids is not None:
        q = q.where(CompFramework.id.in_(list(framework_ids)))
    if not archived:
        q = q.where(CompFramework.archived.is_(False))
    fws = list(db.scalars(q))
    if not fws:
        return []
    ids = [f.id for f in fws]
    areas = list(db.scalars(select(CompArea).where(CompArea.framework_id.in_(ids))
                            .order_by(CompArea.position, CompArea.id)))
    comps = list(db.scalars(select(CompCompetency).where(CompCompetency.framework_id.in_(ids))
                            .order_by(CompCompetency.position, CompCompetency.id)))
    by_area: dict[int, list[dict]] = {}
    for c in comps:
        by_area.setdefault(c.area_id, []).append({"id": c.id, "code": c.code, "title": c.title,
                                                  "descriptors": list(c.descriptors or [])})
    out = []
    for f in fws:
        out.append({"id": f.id, "name": f.name, "subject": f.subject, "description": f.description,
                    "levels": list(f.levels or []), "support_level": f.support_level, "archived": f.archived,
                    "areas": [{"id": a.id, "name": a.name, "competencies": by_area.get(a.id, [])}
                              for a in areas if a.framework_id == f.id]})
    return out


def framework_summary(f: dict) -> dict:
    return {"id": f["id"], "name": f["name"], "subject": f["subject"], "description": f["description"],
            "levels": f["levels"], "support_level": f["support_level"], "archived": f["archived"],
            "areas": len(f["areas"]), "competencies": sum(len(a["competencies"]) for a in f["areas"])}


def create_framework(db: Session, template: dict, user: Any) -> CompFramework:
    """Legt einen Rahmen aus einer normalisierten Vorlage an (Commit macht der Aufrufer)."""
    now = utcnow()
    fw = CompFramework(name=template["name"], subject=template["subject"], description=template["description"],
                       levels=template["levels"], support_level=template["support_level"], archived=False,
                       created_by=getattr(user, "id", None), created_at=now, updated_at=now)
    db.add(fw)
    db.flush()
    for ai, area in enumerate(template["areas"]):
        a = CompArea(framework_id=fw.id, name=area["name"], position=ai)
        db.add(a)
        db.flush()
        for ci, c in enumerate(area["competencies"]):
            db.add(CompCompetency(framework_id=fw.id, area_id=a.id, code=c["code"], title=c["title"],
                                  descriptors=c["descriptors"], position=ci))
    db.flush()
    return fw


def competency_index(db: Session) -> dict[int, dict]:
    """Kompetenz-ID → ``{framework_id, area_id, title, code, levels(max), framework_name, area_name}``."""
    out: dict[int, dict] = {}
    for fw in tree(db, archived=True):
        for a in fw["areas"]:
            for c in a["competencies"]:
                out[c["id"]] = {"id": c["id"], "title": c["title"], "code": c["code"], "framework_id": fw["id"],
                                "framework_name": fw["name"], "area_id": a["id"], "area_name": a["name"],
                                "max_level": len(fw["levels"]), "support_level": fw["support_level"],
                                "archived": fw["archived"]}
    return out


def delete_competencies(db: Session, comp_ids: list[int]) -> None:
    """Löscht Kompetenzen samt Lernständen und Zuordnungen (Pläne bleiben ohne Kompetenz stehen)."""
    if not comp_ids:
        return
    db.execute(delete(CompAssessment).where(CompAssessment.competency_id.in_(comp_ids)))
    db.execute(delete(CompLink).where(CompLink.competency_id.in_(comp_ids)))
    for plan in db.scalars(select(CompPlan).where(CompPlan.competency_id.in_(comp_ids))):
        plan.competency_id = None
    db.execute(delete(CompCompetency).where(CompCompetency.id.in_(comp_ids)))


# ------------------------------------------------------------------------------------------------ Lernstand
def assessment_dict(r: CompAssessment, kind: str) -> dict:
    """Ein Eintrag für die Oberfläche; ``kind``-Sicht = ``staff`` | ``self`` | ``family``."""
    evidence_type = r.evidence_type
    hidden = kind != "staff" and evidence_type == "note"
    return {"id": r.id, "kind": r.kind, "level": r.level, "date": r.assessed_on, "by": r.by_name,
            "evidence_type": "" if hidden else evidence_type,
            "evidence_ref": "" if hidden else r.evidence_ref,
            "evidence": "" if hidden else dec(r.evidence_enc, r.aad("evidence")),
            "comment": dec(r.comment_enc, r.aad("comment")),
            "confirmed": r.confirmed_at is not None, "confirmed_by": r.confirmed_by,
            "created_at": iso(r.created_at)}


def student_rows(db: Session, sid: str, comp_ids: Optional[list[int]] = None) -> list[CompAssessment]:
    q = select(CompAssessment).where(CompAssessment.student_id == sid)
    if comp_ids is not None:
        q = q.where(CompAssessment.competency_id.in_(comp_ids))
    return list(db.scalars(q.order_by(CompAssessment.assessed_on, CompAssessment.id)))


def current_levels(rows: Iterable[CompAssessment]) -> tuple[dict[int, CompAssessment], dict[int, CompAssessment]]:
    """Aktuelle Einträge je Kompetenz: ``(Lehrkraft, Selbsteinschätzung)``."""
    teacher: dict[int, CompAssessment] = {}
    own: dict[int, CompAssessment] = {}
    for r in rows:   # aufsteigend nach Datum/ID → der letzte gewinnt
        target = teacher if r.kind == "teacher" else own
        target[r.competency_id] = r
    return teacher, own


def student_view(db: Session, sid: str, kind: str, framework_ids: Optional[list[int]] = None) -> dict:
    frameworks = tree(db, framework_ids)
    comp_ids = [c["id"] for f in frameworks for a in f["areas"] for c in a["competencies"]]
    rows = student_rows(db, sid, comp_ids)
    teacher, own = current_levels(rows)
    hist: dict[int, list[CompAssessment]] = {}
    for r in rows:
        hist.setdefault(r.competency_id, []).append(r)
    links: dict[int, list[CompLink]] = {}
    for ln in db.scalars(select(CompLink).where(CompLink.competency_id.in_(comp_ids))):
        links.setdefault(ln.competency_id, []).append(ln)
    titles = _item_titles(db, [ln for lst in links.values() for ln in lst]) if kind == "staff" else {}
    out = []
    for f in frameworks:
        n = len(f["levels"])
        f_levels: dict[int, int] = {}
        areas_out = []
        for a in f["areas"]:
            comps_out = []
            a_levels: dict[int, int] = {}
            for c in a["competencies"]:
                t, s = teacher.get(c["id"]), own.get(c["id"])
                if t:
                    a_levels[c["id"]] = f_levels[c["id"]] = t.level
                entry = dict(c)
                entry["teacher"] = assessment_dict(t, kind) if t else None
                entry["self"] = assessment_dict(s, kind) if s else None
                entry["pending"] = bool(s and s.confirmed_at is None)
                entry["history"] = [assessment_dict(r, kind) for r in reversed(hist.get(c["id"], []))]
                entry["links"] = [{"item_type": ln.item_type, "item_id": ln.item_id,
                                   "title": titles.get((ln.item_type, ln.item_id), "")}
                                  for ln in links.get(c["id"], [])]
                if kind == "staff":
                    entry["support"] = logic.needs_support(t.level if t else None, s.level if s else None,
                                                           f["support_level"])
                comps_out.append(entry)
            areas_out.append({"id": a["id"], "name": a["name"], "competencies": comps_out,
                              "progress": round(logic.progress(a_levels, [c["id"] for c in a["competencies"]], n), 3),
                              "assessed": len(a_levels)})
        out.append({**{k: f[k] for k in ("id", "name", "subject", "description", "levels", "support_level")},
                    "areas": areas_out,
                    "progress": round(logic.progress(f_levels, [c["id"] for a in f["areas"] for c in a["competencies"]],
                                                     n), 3),
                    "assessed": len(f_levels),
                    "total": sum(len(a["competencies"]) for a in f["areas"])})
    return {"frameworks": out, "badges": awarded_badges(db, sid, kind == "staff")}


def _item_titles(db: Session, links: list[CompLink]) -> dict[tuple[str, str], str]:
    """Titel zugeordneter Aufgaben/Materialien der Kursräume (nur ``channel_item``; sonst leer)."""
    ids = []
    for ln in links:
        if ln.item_type == "channel_item" and ln.item_id.isdigit():
            ids.append(int(ln.item_id))
    if not ids:
        return {}
    try:
        from schulmanager.server.feature_models.channels import ChannelItem
        rows = db.execute(select(ChannelItem.id, ChannelItem.title).where(ChannelItem.id.in_(ids))).all()
    except Exception:  # noqa: BLE001 - Kursräume sind optional
        return {}
    return {("channel_item", str(i)): t for i, t in rows}


# ------------------------------------------------------------------------------------------------ Abzeichen
def badge_dict(b: CompBadge, awarded: int = 0, text: str = "") -> dict:
    return {"id": b.id, "name": b.name, "description": b.description, "icon": b.icon, "color": b.color,
            "criteria": b.criteria, "criteria_text": text, "auto": bool(b.criteria), "active": b.active,
            "awarded": awarded}


def criteria_text(db: Session, criteria: Optional[dict], idx: Optional[dict[int, dict]] = None) -> str:
    if not criteria:
        return "Wird von der Lehrkraft vergeben"
    idx = idx if idx is not None else competency_index(db)
    n, kind = criteria["min_level"], criteria["type"]
    if kind == "competencies":
        names = [idx[i]["title"] for i in criteria["competency_ids"] if i in idx]
        return f"Stufe {n} in {len(criteria['competency_ids'])} Kompetenz(en): " + "; ".join(names[:4]) + \
            (" …" if len(names) > 4 else "")
    pct = round(criteria["share"] * 100)
    if kind == "area":
        name = next((v["area_name"] for v in idx.values() if v["area_id"] == criteria["area_id"]), "Bereich")
        return f"Stufe {n} bei {pct} % der Kompetenzen im Bereich „{name}“"
    name = next((v["framework_name"] for v in idx.values() if v["framework_id"] == criteria["framework_id"]), "Rahmen")
    return f"Stufe {n} bei {pct} % der Kompetenzen im Rahmen „{name}“"


def awarded_badges(db: Session, sid: str, staff: bool = False) -> list[dict]:
    rows = db.execute(select(CompBadgeAward, CompBadge).join(CompBadge, CompBadge.id == CompBadgeAward.badge_id)
                      .where(CompBadgeAward.student_id == sid).order_by(CompBadgeAward.awarded_on.desc(),
                                                                         CompBadgeAward.id.desc())).all()
    return [{"award_id": a.id, "badge_id": b.id, "name": b.name, "description": b.description, "icon": b.icon,
             "color": b.color, "date": a.awarded_on, "auto": a.auto, "by": a.awarded_by_name if staff else "",
             "note": dec(a.note_enc, a.aad("note"))} for a, b in rows]


def auto_award(db: Session, student_ids: Iterable[str], user: Any = None) -> list[dict]:
    """Prüft die automatischen Abzeichen für die Schüler/innen und vergibt neu erreichte (kein Commit)."""
    badges = [b for b in db.scalars(select(CompBadge).where(CompBadge.active.is_(True))) if b.criteria]
    if not badges:
        return []
    idx = competency_index(db)
    areas: dict[int, list[int]] = {}
    fws: dict[int, list[int]] = {}
    for cid, v in idx.items():
        areas.setdefault(v["area_id"], []).append(cid)
        fws.setdefault(v["framework_id"], []).append(cid)
    out = []
    for sid in dict.fromkeys(student_ids):
        have = set(db.scalars(select(CompBadgeAward.badge_id).where(CompBadgeAward.student_id == sid)))
        todo = [b for b in badges if b.id not in have]
        if not todo:
            continue
        teacher, _own = current_levels(student_rows(db, sid))
        levels = {cid: r.level for cid, r in teacher.items()}
        for b in todo:
            if logic.criteria_met(b.criteria, levels, areas, fws):
                a = CompBadgeAward(badge_id=b.id, student_id=sid, awarded_on=today().isoformat(), awarded_by=None,
                                   awarded_by_name="automatisch", auto=True, note_enc="")
                db.add(a)
                out.append({"student_id": sid, "badge_id": b.id, "name": b.name})
    db.flush()
    return out
