"""Demo-Daten für Kompetenzraster und Lernstand (erfundene Werte).

``seed_demo(school)`` legt – falls noch kein Rahmen existiert – die beiden Beispielrahmen an (Grundschule Mathe/Deutsch,
Montessori-Materialien), Lernstände für die Demo-Schüler/innen und drei Klassen, Selbsteinschätzungen, Lernplan-Einträge
und zwei Abzeichen. Aufruf aus ``demo_loader.load_demo``; mehrfaches Aufrufen ändert nichts.
"""
from __future__ import annotations

import logging
import zlib
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select

from schulmanager import competency as logic

from . import competency_db as cdb
from . import crypto
from .db import session_scope, utcnow
from .feature_models.competency import CompAssessment, CompBadge, CompFramework, CompPlan

log = logging.getLogger("schulmanager.demo")

DEMO_TEACHER = "Lernbegleitung (Demo)"


def _h(*parts: Any) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode())


def _seed_students(school: Any, extra: list[str]) -> list[str]:
    ids: list[str] = list(extra)
    classes = [c.id for c in sorted(school.classes, key=lambda c: (c.grade, c.name))][:3]
    for cid in classes:
        ids.extend(s.id for s in school.students if s.class_id == cid)
    return list(dict.fromkeys(ids))


def seed_demo(school: Any, demo_student_ids: list[str] | None = None) -> dict[str, int]:
    with session_scope() as db:
        if db.scalar(select(func.count(CompFramework.id))):
            return {"frameworks": 0}
        fws = {}
        for key in ("grundschule-mathe-deutsch", "montessori-materialien"):
            fws[key] = cdb.create_framework(db, logic.normalize_template(logic.TEMPLATES[key]), None)
        db.flush()
        tree = {f["id"]: f for f in cdb.tree(db)}
        today = date.today()
        students = _seed_students(school, demo_student_ids or [])
        count = 0
        first_demo = (demo_student_ids or [None])[0]
        for sid in students:
            for key, fw in fws.items():
                f = tree[fw.id]
                n = len(f["levels"])
                for a in f["areas"]:
                    for c in a["competencies"]:
                        seed = _h(sid, c["id"])
                        if seed % 100 < 35 and sid not in (demo_student_ids or []):
                            continue          # nicht alles eingeschätzt
                        level = 1 + seed % n
                        if sid == first_demo and key == "grundschule-mathe-deutsch" and a["name"].startswith("Mathe: Zahlen"):
                            level = max(level, 3)       # das erste Demo-Kind bekommt das automatische Abzeichen
                        day = (today - timedelta(days=seed % 90)).isoformat()
                        row = CompAssessment(student_id=sid, competency_id=c["id"], kind="teacher", level=level,
                                             assessed_on=day, evidence_type="", evidence_ref="", evidence_enc="",
                                             comment_enc="", by_user_id=None, by_name=DEMO_TEACHER,
                                             created_at=utcnow())
                        db.add(row)
                        db.flush()
                        if seed % 7 == 0:
                            row.comment_enc = crypto.encrypt_text("Arbeitet konzentriert und fragt bei Bedarf nach.",
                                                                  row.aad("comment"))
                        count += 1
                        if level > 1 and seed % 5 == 0:       # früherer, niedrigerer Stand (Verlauf)
                            old = CompAssessment(student_id=sid, competency_id=c["id"], kind="teacher",
                                                 level=level - 1, assessed_on=(date.fromisoformat(day)
                                                                               - timedelta(days=40)).isoformat(),
                                                 evidence_type="", evidence_ref="", evidence_enc="", comment_enc="",
                                                 by_user_id=None, by_name=DEMO_TEACHER, created_at=utcnow())
                            db.add(old)
                        if seed % 4 == 1:                      # Selbsteinschätzung, teils unbestätigt
                            own = CompAssessment(student_id=sid, competency_id=c["id"], kind="self",
                                                 level=min(n, level + (1 if seed % 3 == 0 else 0)),
                                                 assessed_on=today.isoformat(), evidence_type="", evidence_ref="",
                                                 evidence_enc="", comment_enc="", by_user_id=None,
                                                 by_name="", created_at=utcnow())
                            if seed % 8 == 1:
                                own.confirmed_at, own.confirmed_by = utcnow(), DEMO_TEACHER
                            db.add(own)
        monday = logic.week_start(today).isoformat()
        for sid in (demo_student_ids or [])[:3]:
            f = tree[fws["grundschule-mathe-deutsch"].id]
            for i, c in enumerate([c for a in f["areas"] for c in a["competencies"]][:4]):
                p = CompPlan(student_id=sid, competency_id=c["id"], title_enc="", note_enc="", week_start=monday,
                             due_date=(today + timedelta(days=2 + i)).isoformat(),
                             status=("erledigt", "in_arbeit", "offen", "offen")[i], source="lehrkraft", item_type="",
                             item_id="", created_at=utcnow(), updated_at=utcnow())
                db.add(p)
                db.flush()
                p.title_enc = crypto.encrypt_text(c["title"], p.aad("title"))
        gs = tree[fws["grundschule-mathe-deutsch"].id]
        math = next(a for a in gs["areas"] if a["name"].startswith("Mathe: Zahlen"))
        db.add(CompBadge(name="Rechenprofi", description="Zahlen und Rechnen sicher beherrscht.", icon="calculator",
                         color="gold", criteria={"type": "area", "area_id": math["id"], "min_level": 3, "share": 0.8}))
        db.add(CompBadge(name="Lesefuchs", description="Für besondere Freude am Lesen (von der Lehrkraft vergeben).",
                         icon="book", color="green", criteria=None))
        db.flush()
        awards = cdb.auto_award(db, students, None)
        return {"frameworks": len(fws), "assessments": count, "badges": len(awards)}
