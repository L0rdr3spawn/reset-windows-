"""Demo-Daten für Abstimmung, Umfrage und Selbsttest (Doku: docs/LERNAKTIVITAETEN.md §9).

In je einem Demo-Klassenraum (5a, 7a – falls vorhanden) entstehen erfundene Beispiele: eine Fragensammlung mit sechs
Fragen (je Art eine, eine mit Formel), ein offener Selbsttest mit einigen beendeten Versuchen, eine namentliche
Abstimmung mit Stimmen und eine anonyme Umfrage mit Antworten. Aufruf: :func:`seed_demo` (von ``demo_loader.load_demo``).
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select

from schulmanager import channels as chx
from schulmanager import forms as fx
from schulmanager import learning as lx

from . import learning_service as ls
from .db import session_scope, utcnow
from .db_models import User
from .feature_models.learning import (LearningPoll, LearningQuestion, LearningSelftest, LearningSurvey,
                                      LearningSurveyParticipant, LearningSurveyResponse)

DEMO_CLASSES = ("5a", "7a")

QUESTIONS = [
    {"type": "single", "text": "Wie viel ist $\\frac{1}{2} + \\frac{1}{4}$?", "points": 2, "category": "Brüche",
     "options": [{"text": "$\\frac{3}{4}$", "correct": True, "feedback": "Gleichnamig machen: $\\frac{2}{4} + \\frac{1}{4}$."},
                 {"text": "$\\frac{2}{6}$"}, {"text": "$\\frac{1}{8}$"}]},
    {"type": "multi", "text": "Welche Zahlen sind Primzahlen?", "points": 2, "category": "Zahlen",
     "options": [{"text": "2", "correct": True}, {"text": "9"}, {"text": "11", "correct": True}, {"text": "15"}]},
    {"type": "truefalse", "text": "Ein Quadrat hat vier gleich lange Seiten.", "correct": True, "points": 1,
     "category": "Geometrie"},
    {"type": "cloze", "text": "Die Hauptstadt von Deutschland ist ___.", "gaps": [["Berlin"]], "points": 1,
     "category": "Erdkunde"},
    {"type": "matching", "text": "Ordne den Tieren ihre Laute zu.", "points": 3, "category": "Sachunterricht",
     "pairs": [{"left": "Hund", "right": "bellt"}, {"left": "Katze", "right": "miaut"}, {"left": "Kuh", "right": "muht"}]},
    {"type": "numeric", "text": "Wie groß ist der Umfang eines Quadrats mit der Seitenlänge 2,5 cm?", "value": 10,
     "tolerance": 0.1, "unit": "cm", "points": 2, "category": "Geometrie"},
]

SURVEY_FIELDS = [
    {"id": "klar", "type": "scale", "label": "Wie verständlich war der Unterricht?", "low": "gar nicht", "high": "sehr"},
    {"id": "tempo", "type": "select", "label": "Das Tempo war", "options": ["zu schnell", "genau richtig", "zu langsam"]},
    {"id": "gut", "type": "multiselect", "label": "Was hilft mir beim Lernen?",
     "options": ["Beispiele", "Übungsaufgaben", "Gruppenarbeit", "Erklärvideos"]},
    {"id": "weiter", "type": "yesno", "label": "Würde ich diese Form der Aufgaben weiterempfehlen?"},
    {"id": "text", "type": "textarea", "label": "Was wünsche ich mir noch?"},
]


def _wrong(q: dict) -> Any:
    kind = q["type"]
    if kind == "single":
        return next(i for i, o in enumerate(q["options"]) if not o["correct"])
    if kind == "multi":
        return [next(i for i, o in enumerate(q["options"]) if not o["correct"])]
    if kind == "truefalse":
        return not q["correct"]
    if kind == "cloze":
        return ["Hamburg"] * len(q["gaps"])
    if kind == "matching":
        n = len(lx.matching_rights(q))
        return {str(i): (i + 1) % n for i in range(len(q["pairs"]))}
    return str(q["value"] + 7)


def _right(q: dict) -> Any:
    kind = q["type"]
    if kind in ("single", "multi"):
        right = [i for i, o in enumerate(q["options"]) if o["correct"]]
        return right[0] if kind == "single" else right
    if kind == "truefalse":
        return q["correct"]
    if kind == "cloze":
        return [g[0] for g in q["gaps"]]
    if kind == "matching":
        rights = lx.matching_rights(q)
        return {str(i): rights.index(p["right"]) for i, p in enumerate(q["pairs"])}
    return str(q["value"]).replace(".", ",")


def _seed_class(db, school, class_id: str, rng: random.Random) -> dict[str, int]:
    from .routes.features_channels import _ensure_rows

    stats = {"questions": 0, "tests": 0, "attempts": 0, "polls": 0, "votes": 0, "surveys": 0, "responses": 0}
    spec = chx.channel_spec(school, "class", class_id)
    if spec is None:
        return stats
    channel = _ensure_rows(db, [spec]).get(("class", class_id))
    if channel is None or db.scalar(select(LearningSelftest.id).where(LearningSelftest.channel_id == channel.id)):
        return stats
    teacher = db.scalar(select(User).where(User.role == "lehrer", User.active.is_(True),
                                           User.teacher_id.in_(sorted(spec.teacher_ids)))) if spec.teacher_ids else None
    created_by = teacher.id if teacher else None
    sids = chx.channel_student_ids(school, "class", class_id)
    pupils = list(db.scalars(select(User).where(User.role == "schueler", User.active.is_(True),
                                                User.student_id.in_(list(sids))).order_by(User.id).limit(12))) \
        if sids else []

    # --- Fragensammlung + Selbsttest
    rows = []
    for raw in QUESTIONS:
        data = lx.normalize_question(raw)
        row = LearningQuestion(channel_id=channel.id, qtype=data["type"], category=data["category"],
                               created_by=created_by, created_at=utcnow())
        db.add(row)
        db.flush()
        ls.write_json(row, "data", data)
        rows.append((row, data))
        stats["questions"] += 1
    test = LearningSelftest(channel_id=channel.id, title="Mathe und mehr – Selbsttest", status="offen",
                            question_ids=[r.id for r, _d in rows], max_attempts=3, time_limit_min=20,
                            shuffle_questions=True, shuffle_answers=True, immediate_feedback=False, review="full",
                            pass_percent=60.0, created_by=created_by, created_at=utcnow())
    db.add(test)
    db.flush()
    test.write_text("description", "Sechs kurze Fragen zum Üben. Sie können den Test bis zu dreimal machen; der beste Versuch zählt.")
    stats["tests"] += 1
    for i, pupil in enumerate(pupils[:6]):
        for number in range(1 + (i % 2)):
            att = ls.start_attempt(db, test, pupil.id)
            answers = {}
            skill = 0.35 + 0.12 * (i + number)
            for item in ls.attempt_snapshot(att):
                if rng.random() < 0.12 * (i % 3):
                    continue                                  # einzelne Fragen bleiben offen
                q = item["q"]
                answers[str(item["qid"])] = _right(q) if rng.random() < min(skill, 0.95) else _wrong(q)
            ls.save_attempt_state(att, {"answers": answers, "checked": []})
            ls.finish_attempt(att)
            att.started_at = utcnow() - timedelta(days=2 + number, minutes=rng.randrange(5, 15))
            att.finished_at = att.started_at + timedelta(minutes=rng.randrange(4, 12))
            stats["attempts"] += 1

    # --- Abstimmung (namentlich)
    poll = LearningPoll(channel_id=channel.id, option_count=3, multiple=False, anonymous=False, results="live",
                        created_by=created_by, created_at=utcnow(), ends_at=utcnow() + timedelta(days=7))
    db.add(poll)
    db.flush()
    poll.write_text("question", "Wohin soll unser Ausflug im Frühjahr gehen?")
    ls.write_json(poll, "options", ["Zoo", "Museum", "Waldspielplatz"])
    stats["polls"] += 1
    for i, pupil in enumerate(pupils[:8]):
        ls.cast_vote(db, poll, pupil.id, [i % 3 if i % 4 else 0])
        stats["votes"] += 1

    # --- Umfrage (anonym)
    survey = LearningSurvey(channel_id=channel.id, title="Feedback zum Unterricht", fields=fx.normalize_fields(
        SURVEY_FIELDS, allowed=lx.SURVEY_FIELD_TYPES), anonymous=True, status="offen", results_to_students=True,
        created_by=created_by, created_at=utcnow(), closes_at=utcnow() + timedelta(days=14))
    db.add(survey)
    db.flush()
    survey.write_text("intro", "Ihre Antworten sind anonym. Danke, dass Sie mitmachen!")
    stats["surveys"] += 1
    wishes = ["Mehr Gruppenarbeit.", "Gern öfter kleine Tests zum Üben.", "", "Mehr Zeit für Aufgaben."]
    for i, pupil in enumerate(pupils[:7]):
        answers = fx.clean_answers({"fields": survey.fields}, {
            "klar": 3 + (i % 3), "tempo": ["genau richtig", "zu schnell", "genau richtig"][i % 3],
            "gut": [["Beispiele"], ["Beispiele", "Übungsaufgaben"], ["Gruppenarbeit"]][i % 3], "weiter": i % 4 != 0,
            "text": wishes[i % len(wishes)]}, student_id=None, periods=0, today=date.today())
        db.add(LearningSurveyParticipant(survey_id=survey.id, user_id=pupil.id))
        resp = LearningSurveyResponse(survey_id=survey.id, user_id=None,
                                      created_at=utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
        db.add(resp)
        db.flush()
        ls.write_json(resp, "answers", answers)
        stats["responses"] += 1
    return stats


def seed_demo(school) -> dict[str, Any]:
    """Legt die Beispiele an (nur, wo es noch keinen Selbsttest gibt). Gibt Zähler zurück."""
    total: dict[str, int] = {}
    have = {c.id for c in school.classes}
    with session_scope() as db:
        for class_id in DEMO_CLASSES:
            if class_id not in have:
                continue
            for key, value in _seed_class(db, school, class_id, random.Random(f"lernen|{class_id}")).items():
                total[key] = total.get(key, 0) + value
    return total
