"""Demo-Schule laden (``POST /admin/demo``, ``SM_LOAD_DEMO=1``) inkl. Demo-Konten.

Demo-Konten (Passwort für alle: ``demo123456``; in development ohne Passwortwechsel-Zwang):
``schulleitung``, ``planer``, ``sekretariat``, ``lehrer1``–``lehrer3`` (erste drei Lehrkräfte),
``schueler1``–``schueler3`` (je ein Schüler aus Jg. 5, 9/Praxisklasse, Oberstufe), ``eltern1``
(Kinder von schueler1 und schueler2), ``monitor`` (Standort S1). ``admin`` entsteht beim Bootstrap.

Mit ``SM_DEMO_ALL_ACCOUNTS`` (Standard an) bekommt außerdem jede Lehrkraft, jede/r Schüler/in und jedes Elternhaus
ein Konto (gleiches Passwort): ``l-<kürzel>``, ``s-<schüler-id>``, ``e-<schüler-id>`` – damit sich Postfach und Chats
mit beliebigen Personen ausprobieren lassen.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import select

from ..demo import build_demo
from ..models import School
from ..planning import assign_class_teachers, assign_teachers
from ..scheduler import generate
from .config import config
from .db import session_scope
from .db_models import ParentLink, User
from .events import bus
from .security import hash_password

log = logging.getLogger("schulmanager.demo")

DEMO_PASSWORD = "demo123456"


def build_demo_school(time_limit: float | None = None, classes_per_grade: int = 14,
                      progress=None) -> tuple[School, dict]:
    """Baut die Demo-Schule und generiert den Stundenplan (CPU-intensiv, ``time_limit`` Sekunden)."""
    t0 = time.monotonic()
    school = build_demo(classes_per_grade=classes_per_grade)
    warnings = assign_teachers(school)
    # Klassenleitungen (Atteste/Krankmeldungen, §9.6); Demo-Konten lehrer1–3 bevorzugt
    assign_class_teachers(school, prefer=[t.id for t in school.teachers][:3])
    result = generate(school, time_limit=config.generate_time_limit if time_limit is None else time_limit,
                      progress=progress)
    school.lessons = result.lessons
    warnings += result.warnings
    try:  # Pausenaufsichten, falls das Modul des Agenten Vertretung vorhanden ist
        from ..duties import generate_duties  # type: ignore[import-not-found]

        school.duties = generate_duties(school)
    except Exception as exc:  # noqa: BLE001
        log.info("Pausenaufsichten nicht erzeugt: %s", exc)
    stats = {"classes": len(school.classes), "teachers": len(school.teachers), "students": len(school.students),
             "lessons": len(school.lessons), "unplaced": len(result.unplaced),
             "seconds": round(time.monotonic() - t0, 1),
             "warnings": warnings[:50]}
    return school, stats


def _pick_students(school: School, lead_class: str | None = None) -> list[str]:
    """Demo-Schüler/innen: Jg. 5, Praxisklasse, Oberstufe (bevorzugt die Klasse, die ``lehrer1`` leitet – so lässt
    sich die Sicht der Klassenleitung auf Krankmeldungen und Atteste mit Demo-Konten vorführen)."""
    by_class: dict[str, list[str]] = {}
    for s in school.students:
        by_class.setdefault(s.class_id, []).append(s.id)
    picks: list[str] = []
    upper = ([lead_class] if lead_class and lead_class.startswith("Q") else []) + ["Q1-1", "Q2-1"]
    for prefs in (["5a"], ["9P", "9a"], upper):
        for cid in prefs:
            if by_class.get(cid):
                picks.append(by_class[cid][0])
                break
    for s in school.students:  # Auffüllen, falls Klassen fehlen
        if len(picks) >= 3:
            break
        if s.id not in picks:
            picks.append(s.id)
    return picks[:3]


def _student_of_teacher(school: School, teacher_id: str) -> str | None:
    """Ein/e Schüler/in, die/der einen Kursteil der Lehrkraft besucht (bevorzugt Oberstufe, für Kursräume)."""
    from ..timetable import student_parts

    taught = {(c.id, i) for c in school.courses for i, p in enumerate(c.parts) if p.teacher == teacher_id}
    if not taught:
        return None
    course_ids = {c for c, _ in taught}
    classes = {cid for c in school.courses if c.id in course_ids for cid in c.classes}
    for s in sorted((s for s in school.students if s.class_id in classes), key=lambda s: (not s.courses, s.id)):
        parts = student_parts(school, s.id)
        if any((cid, i) in taught for cid, idx in parts.items() for i in idx):
            return s.id
    return None


def demo_account_specs(school: School) -> list[dict[str, Any]]:
    teachers = [t.id for t in school.teachers][:3]
    lead = next((c.id for c in school.classes if teachers and c.class_teacher == teachers[0]), None)
    students = _pick_students(school, lead)
    names = {s.id: s.name for s in school.students}
    tnames = {t.id: t.name for t in school.teachers}
    sites = [s.id for s in school.sites]
    specs: list[dict[str, Any]] = [
        {"username": "schulleitung", "role": "schulleitung", "display_name": "Schulleitung (Demo)"},
        {"username": "planer", "role": "planer", "display_name": "Stundenplanung (Demo)"},
        {"username": "sekretariat", "role": "sekretariat", "display_name": "Sekretariat (Demo)"},
    ]
    for i, tid in enumerate(teachers, 1):
        specs.append({"username": f"lehrer{i}", "role": "lehrer", "display_name": tnames[tid], "teacher_id": tid})
    for i, sid in enumerate(students, 1):
        # schueler3 (Oberstufe) ist volljährig: darf sich selbst krankmelden und Atteste einreichen (§9.6)
        specs.append({"username": f"schueler{i}", "role": "schueler", "display_name": names[sid], "student_id": sid,
                      "adult": i == 3})
    lk = _student_of_teacher(school, teachers[0]) if teachers else None
    if lk and lk not in students:  # Kursräume vorführen: Schüler/in im Kurs von lehrer1
        specs.append({"username": "schueler4", "role": "schueler", "display_name": names[lk], "student_id": lk})
    if students:
        specs.append({"username": "eltern1", "role": "eltern", "display_name": "Familie (Demo)",
                      "children": students[:2]})
    specs.append({"username": "monitor", "role": "monitor", "display_name": "Monitor Hauptstandort",
                  "site": sites[0] if sites else None})
    specs.append({"username": "zuschauer", "role": "zuschauer", "display_name": "Zuschauer/in (Demo)"})
    return specs


def _demo_contact(db, user: User) -> None:
    """Bestätigte Demo-Adresse ``<benutzer>@demo.schule`` (zum Ausprobieren von „Passwort vergessen“ im
    Test-Postausgang, §11.2)."""
    from .db import utcnow
    from .feature_models.contact import UserContact

    user.email = f"{user.username}@demo.schule"
    contact = db.get(UserContact, user.id) or UserContact(user_id=user.id)
    contact.email_verified_value = user.email
    contact.email_verified_at = contact.updated_at = utcnow()
    db.add(contact)


# Demo-Zugänge (``SM_DEMO_PUBLIC``): Art → (Vorlage-Konto, Beschriftung). Ein ausgegebenes Konto übernimmt Rolle und
# Verknüpfungen der Vorlage (Lehrkraft, Kind, Kinder der Eltern, Standort) – so sieht es dieselben simulierten Daten.
DEMO_ACCESS_KINDS = {
    "admin": ("admin", "Administration"), "schulleitung": ("schulleitung", "Schulleitung"),
    "planer": ("planer", "Stundenplanung"), "sekretariat": ("sekretariat", "Sekretariat"),
    "lehrer": ("lehrer1", "Lehrkraft (Klassenleitung)"), "lehrer2": ("lehrer2", "Lehrkraft"),
    "schueler": ("schueler1", "Schüler/in"), "schueler_volljaehrig": ("schueler3", "Schüler/in, volljährig"),
    "eltern": ("eltern1", "Eltern"), "monitor": ("monitor", "Vertretungsmonitor"),
    "zuschauer": ("zuschauer", "Zuschauer/in (nur lesen)"),
}
DEMO_ACCESS_PREFIX = "dz-"
_BUILTIN = {"lehrer1", "lehrer2", "lehrer3", "schueler1", "schueler2", "schueler3", "schueler4", "eltern1",
            "schulleitung", "planer", "sekretariat", "monitor", "zuschauer"}


def is_demo_account(username: str) -> bool:
    """Vorgegebene Demo-Konten (inkl. ``l-``/``s-``/``e-``-Konten aller Personen, ausgegebene ``dz-``-Zugänge, Inhaber)
    – in der Vorführ-Instanz gegen Änderungen geschützt."""
    return username in _BUILTIN or username == config.admin_user or username.startswith(
        ("l-", "s-", "e-", DEMO_ACCESS_PREFIX))


def create_demo_accounts(school: School) -> list[dict[str, Any]]:
    """Legt fehlende Demo-Konten an bzw. aktualisiert deren Verknüpfungen. Gibt die Kontenliste zurück."""
    must_change = config.is_production
    pw_hash = hash_password(DEMO_PASSWORD)
    out = []
    with session_scope() as db:
        for spec in demo_account_specs(school):
            user = db.scalar(select(User).where(User.username == spec["username"]))
            if user is None:
                user = User(username=spec["username"], role=spec["role"], display_name=spec["display_name"],
                            password_hash=pw_hash, must_change_password=must_change, active=True,
                            totp_enabled=False, adult=bool(spec.get("adult")))
                db.add(user)
                created = True
            else:
                created = False
            if user.role == spec["role"]:
                user.teacher_id = spec.get("teacher_id", user.teacher_id)
                user.student_id = spec.get("student_id", user.student_id)
                user.site = spec.get("site", user.site)
                if spec.get("display_name") and created:
                    user.display_name = spec["display_name"]
            db.flush()
            if created and not user.email and user.role != "monitor":
                _demo_contact(db, user)
            if spec.get("children") and user.role == "eltern":
                existing = set(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user.id)))
                for sid in spec["children"]:
                    if sid not in existing:
                        db.add(ParentLink(parent_user_id=user.id, student_id=sid))
            out.append({"username": user.username, "role": user.role, "display_name": user.display_name,
                        "password": DEMO_PASSWORD if created else None, "created": created,
                        "teacher_id": user.teacher_id, "student_id": user.student_id,
                        "student_ids": spec.get("children")})
    return out


def create_directory_accounts(school: School) -> dict[str, int]:
    """Demo: Konten für alle Lehrkräfte, Schüler/innen und je ein Elternkonto (falls noch nicht verknüpft)."""
    must_change = config.is_production
    pw_hash = hash_password(DEMO_PASSWORD)
    made = {"lehrer": 0, "schueler": 0, "eltern": 0}
    with session_scope() as db:
        names = set(db.scalars(select(User.username)))
        linked_t = set(db.scalars(select(User.teacher_id).where(User.teacher_id.is_not(None))))
        linked_s = set(db.scalars(select(User.student_id).where(User.student_id.is_not(None))))
        parented = set(db.scalars(select(ParentLink.student_id)))
        new_parents: list[tuple[User, str]] = []

        def add(username: str, role: str, display: str, **kw: Any) -> User | None:
            if username in names:
                return None
            names.add(username)
            u = User(username=username, role=role, display_name=display[:120], password_hash=pw_hash,
                     must_change_password=must_change, active=True, totp_enabled=False, adult=False, **kw)
            db.add(u)
            made[role] += 1
            return u

        for t in school.teachers:
            if t.id not in linked_t:
                add(f"l-{t.id.lower()}", "lehrer", t.name or t.id, teacher_id=t.id)
        for s in school.students:
            if s.id not in linked_s:
                add(f"s-{s.id.lower()}", "schueler", s.name or s.id, student_id=s.id)
            if s.id not in parented:
                u = add(f"e-{s.id.lower()}", "eltern", f"Eltern von {s.name or s.id}")
                if u is not None:
                    new_parents.append((u, s.id))
        db.flush()
        for u, sid in new_parents:
            db.add(ParentLink(parent_user_id=u.id, student_id=sid))
    return made


def load_demo(user: Any = None, time_limit: float | None = None, accounts: bool = True,
              classes_per_grade: int = 14) -> dict[str, Any]:
    """Baut die Demo, ersetzt das Planungsdokument (neue Version) und legt Demo-Konten an."""
    from .store import get_store

    def progress(msg: str, frac: float) -> None:
        bus.publish("job", {"id": "demo", "status": "running", "progress": round(frac, 3), "message": msg},
                    permission="system.admin")

    bus.publish("job", {"id": "demo", "status": "running", "progress": 0.0, "message": "Demo-Schule wird erzeugt"},
                permission="system.admin")
    try:
        school, stats = build_demo_school(time_limit, classes_per_grade, progress)
        version = get_store().replace(user, "Demo-Schule geladen", school, ["all"], action="plan.demo")
        demo_accounts = create_demo_accounts(school) if accounts else []
        if accounts and config.demo_all_accounts:
            log.info("Demo-Konten für alle Personen: %s", create_directory_accounts(school))
        try:   # Benachrichtigungszentrale (M6): erfundene Beispiel-Meldungen für die Glocke
            from .notifications_demo import seed_demo as seed_notifications
            log.info("Demo-Benachrichtigungen: %s", seed_notifications(demo_accounts))
        except Exception:  # noqa: BLE001
            log.exception("Demo-Benachrichtigungen konnten nicht angelegt werden")
        try:   # Notenbuch: erfundene Noten für einige Demoklassen (docs/NOTENBUCH.md §10)
            from .gradebook_demo import seed_demo
            log.info("Demo-Notenbuch: %s", seed_demo(school))
        except Exception:  # noqa: BLE001 - Demo-Noten dürfen das Laden der Demo nie verhindern
            log.exception("Demo-Notenbuch konnte nicht angelegt werden")
        try:   # Kompetenzraster (M5): Beispielrahmen und Lernstände; Fehler dürfen das Laden der Demo nicht stoppen
            from .competency_seed import seed_demo
            log.info("Demo-Kompetenzraster: %s", seed_demo(school, [a["student_id"] for a in demo_accounts if a.get("student_id")]))
        except Exception:  # noqa: BLE001
            log.exception("Demo-Kompetenzraster konnten nicht angelegt werden")
        try:   # Lernaktivitäten (M3): Abstimmung, Umfrage, Fragensammlung und Selbsttest in Demo-Klassenräumen
            from .learning_demo import seed_demo as seed_learning
            log.info("Demo-Lernaktivitäten: %s", seed_learning(school))
        except Exception:  # noqa: BLE001
            log.exception("Demo-Lernaktivitäten konnten nicht angelegt werden")
    except Exception as exc:
        bus.publish("job", {"id": "demo", "status": "failed", "progress": 1.0, "message": str(exc)},
                    permission="system.admin")
        raise
    bus.publish("job", {"id": "demo", "status": "done", "progress": 1.0, "message": "Demo-Schule geladen"},
                permission="system.admin")
    log.info("Demo-Schule geladen: Version %s, %s", version, {k: v for k, v in stats.items() if k != "warnings"})
    if demo_accounts:
        log.warning("Demo-Konten (Passwort %r): %s", DEMO_PASSWORD, ", ".join(a["username"] for a in demo_accounts))
    return {"version": version, "stats": stats, "accounts": demo_accounts}
