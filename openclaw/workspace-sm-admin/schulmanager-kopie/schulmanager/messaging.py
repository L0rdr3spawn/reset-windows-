"""Internes Postfach – reine Logik (ARCHITECTURE.md §9.5): Empfängerauflösung, Rechte, Adressbuch.

Dieses Modul kennt weder Datenbank noch HTTP. Die Server-Routen (``server/routes/features_messages.py``) laden

* die Konten in ein :class:`Directory` (nur erreichbare Konten: aktiv **und** mit ``messages.use`` – deaktivierte
  Konten und Monitor-Konten sind nie Empfänger),
* das Planungsdokument in einen :class:`SchoolIndex` (Klassen, Kurse, Lehrkräfte, Standorte)

und fragen dann hier nach:

* :func:`check_direct` – darf der Absender dieser Einzelperson schreiben? Grundsatz: **alle (``messages.use``) dürfen
  jedem einzelnen Konto schreiben**; Ausnahmen: ``settings.messaging_students_to_students = False`` (Schüler → Schüler),
  Blockierungen, deaktivierte Konten, Monitor-Konten, das eigene Konto.
* :func:`check_group` – Gruppen (Klasse, Eltern einer Klasse, Lehrkräfte einer Klasse, Kurs/Kursteil, Jahrgang,
  Eltern eines Jahrgangs, Kollegium, alle Schüler/innen, alle Eltern, ganze Schule – jeweils optional je Standort)
  nur mit ``messages.broadcast``; Lehrkräfte (Scope ``own_classes``) nur eigene Klassen und eigene Kurse/Kursteile.
* :func:`group_members`, :func:`group_label`, :func:`allowed_groups` – Auflösung, Beschriftung, Adressbuch-Gruppen.
* :func:`search_people`, :func:`person_card` – datensparsames Adressbuch: Schüler/innen und Eltern sehen von anderen nur
  Name, Rolle und Klasse; Lehrkräfte sehen Kindernamen von Eltern nur für eigene Klassen.
* :func:`can_block` – Schulpersonal kann nicht blockiert werden (Probleme → Melden/Moderation).

Gruppen werden als ``(kind, ref)`` adressiert, z. B. ``("class", "5a")``, ``("class_parents", "5a")``,
``("course", "M-5a")`` (ganzer Kurs) bzw. ``("course", "REL-5a-5b#1")`` (Kursteil), ``("grade", "5")``,
``("staff", "")`` (ganzes Kollegium) bzw. ``("staff", "S1")`` (Kollegium eines Standorts).
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Optional

from schulmanager.models import Course, School
from schulmanager.server.permissions import ROLE_LABELS, ROLE_PERMISSIONS, STAFF_ROLES, scope_for

USE_PERMISSION = "messages.use"
BROADCAST_PERMISSION = "messages.broadcast"
MODERATE_PERMISSION = "messages.moderate"

#: Rollen, die das Postfach nutzen (und damit Empfänger sein) können – Monitor-Konten nicht.
MESSAGING_ROLES: frozenset[str] = frozenset(r for r, perms in ROLE_PERMISSIONS.items() if USE_PERMISSION in perms)
#: „Kollegium“: Lehrkräfte, Schulleitung, Stundenplanung, Sekretariat (technische Admin-Konten nicht)
COLLEGIUM_ROLES: frozenset[str] = frozenset({"lehrer", "schulleitung", "planer", "sekretariat"})

# Grenzen (Eingaben werden zusätzlich per Pydantic geprüft)
MAX_SUBJECT = 200
MAX_BODY = 20_000
MAX_ATTACHMENTS = 10
MAX_INDIVIDUALS = 25           # Einzelempfänger ohne messages.broadcast
MAX_INDIVIDUALS_BROADCAST = 200
MAX_GROUPS = 30
MAX_RECIPIENTS = 20_000
# Missbrauchsschutz: neue Unterhaltungen je Stunde bzw. Nachrichten je 10 Minuten
RATE_NEW_CONVERSATIONS = {"staff": 120, "default": 30}
RATE_MESSAGES = {"staff": 300, "default": 60}

GROUP_KINDS: tuple[str, ...] = ("class", "class_parents", "class_lead", "class_teachers", "course", "grade",
                                "grade_parents", "staff", "teachers", "class_leads", "role", "students", "parents",
                                "school")
#: Gruppenarten, die Lehrkräfte (Scope ``own_classes``) für eigene Klassen/Kurse nutzen dürfen
TEACHER_GROUP_KINDS: frozenset[str] = frozenset({"class", "class_parents", "class_lead", "class_teachers", "course"})
SITE_GROUP_KINDS: frozenset[str] = frozenset({"staff", "teachers", "class_leads", "students", "parents", "school"})
#: Rollen-Gruppen (``("role", "schulleitung")``) – nur mit uneingeschränktem ``messages.broadcast``
ROLE_GROUP_ROLES: tuple[str, ...] = ("schulleitung", "sekretariat", "planer", "admin")
CLASS_KINDS: frozenset[str] = frozenset({"class", "class_parents", "class_lead", "class_teachers"})
GROUP_CATEGORY = {"class": "klasse", "class_parents": "klasse", "class_lead": "klasse", "class_teachers": "klasse",
                  "course": "kurs", "grade": "jahrgang", "grade_parents": "jahrgang", "staff": "schule",
                  "teachers": "rolle", "class_leads": "rolle", "role": "rolle", "students": "schule",
                  "parents": "schule", "school": "schule"}
CATEGORY_LABELS = {"schule": "Schule", "rolle": "Rolle", "jahrgang": "Jahrgang", "klasse": "Klasse", "kurs": "Kurs"}
_CATEGORY_ORDER = {"schule": 0, "rolle": 1, "jahrgang": 2, "klasse": 3, "kurs": 4}
_KIND_ORDER = {k: i for i, k in enumerate(GROUP_KINDS)}

REPLY_MODES = ("all", "sender", "none")
REPLY_MODE_LABELS = {"all": "Antworten an alle", "sender": "Antworten nur an mich", "none": "Keine Antworten"}


class MessagingError(Exception):
    """Fachlicher Fehler (wird von den Routen in ``HTTPException(status, message)`` übersetzt)."""

    def __init__(self, message: str, status: int = 403, code: str = "forbidden") -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


# --------------------------------------------------------------------------- Texte
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b\u200e\u200f\u202a-\u202e\u2066-\u2069]")  # ZWJ/ZWNJ bleiben (Emoji-Folgen)
_SPACES_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Für Suche/Vergleich: ohne Akzente, klein (``"Müller"`` → ``"muller"``; ``ß`` → ``ss``)."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()


def clean_subject(text: str) -> str:
    """Betreff: eine Zeile, ohne Steuerzeichen, Leerraum zusammengefasst."""
    return _SPACES_RE.sub(" ", _CONTROL_RE.sub("", text or "")).strip()[:MAX_SUBJECT]


def clean_body(text: str) -> str:
    """Nachrichtentext: Zeilenumbrüche vereinheitlicht, Steuer- und Richtungszeichen entfernt, außen getrimmt."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_RE.sub("", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def query_tokens(query: str) -> list[str]:
    return [t for t in normalize(query).split() if t]


def snippet(text: str, query: str, width: int = 140) -> str:
    """Ausschnitt um den ersten Treffer (für Suchergebnisse)."""
    flat = _SPACES_RE.sub(" ", text or "").strip()
    if len(flat) <= width:
        return flat
    tokens = query_tokens(query)
    pos = -1
    low = normalize(flat)
    for t in tokens:
        pos = low.find(t)
        if pos >= 0:
            break
    if pos < 0:
        return flat[:width - 1].rstrip() + "…"
    start = max(0, pos - width // 3)
    end = min(len(flat), start + width)
    start = max(0, end - width)
    out = flat[start:end].strip()
    return ("…" if start > 0 else "") + out + ("…" if end < len(flat) else "")


def matches(texts: Iterable[str], query: str) -> bool:
    """Alle Suchwörter kommen (akzent-/großschreibungsunabhängig) in den Texten vor."""
    tokens = query_tokens(query)
    if not tokens:
        return True
    hay = " ".join(normalize(t) for t in texts if t)
    return all(t in hay for t in tokens)


def natural_key(text: str) -> tuple:
    """Sortierschlüssel „5a < 10a“."""
    return tuple(int(p) if p.isdigit() else p for p in re.split(r"(\d+)", normalize(text)))


# --------------------------------------------------------------------------- Absender (AuthUser o. ä.)
def has(user: Any, perm: str) -> bool:
    return perm in (getattr(user, "permissions", None) or set())


def perm_scope(user: Any, perm: str) -> Optional[str]:
    fn = getattr(user, "scope", None)
    if callable(fn):
        return fn(perm)
    return scope_for(getattr(user, "role", ""), perm)


def is_staff(user_or_account: Any) -> bool:
    return getattr(user_or_account, "role", "") in STAFF_ROLES


def rate_class(user: Any) -> str:
    return "staff" if is_staff(user) else "default"


# --------------------------------------------------------------------------- Konten
@dataclass(frozen=True)
class Account:
    """Ein Konto aus Sicht des Postfachs (Ausschnitt aus ``users`` + Elternverknüpfungen)."""
    id: int
    role: str
    name: str
    active: bool = True
    teacher_id: Optional[str] = None
    student_id: Optional[str] = None
    site: Optional[str] = None
    children: tuple[str, ...] = ()

    @property
    def reachable(self) -> bool:
        """Kann Nachrichten empfangen (aktiv, Rolle mit ``messages.use``)."""
        return bool(self.active) and self.role in MESSAGING_ROLES

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)


class Directory:
    """Konten mit Indizes für die Gruppenauflösung (es werden nur erreichbare Konten indiziert)."""

    def __init__(self, accounts: Iterable[Account], routing: Optional[dict[str, str]] = None) -> None:
        # routing: {schüler_id: "self"|"parents"} – volljährige Schüler/innen, deren Rundschreiben nur an sie selbst
        # bzw. nur an die Eltern gehen sollen (``parent_access.delivery_routing``); sonst erhalten beide
        self.routing: dict[str, str] = dict(routing or {})
        self.by_id: dict[int, Account] = {a.id: a for a in accounts}
        self.by_student: dict[str, list[int]] = defaultdict(list)
        self.by_teacher: dict[str, list[int]] = defaultdict(list)
        self.parents_of: dict[str, list[int]] = defaultdict(list)
        self.by_role: dict[str, list[int]] = defaultdict(list)
        for a in self.by_id.values():
            if not a.reachable:
                continue
            self.by_role[a.role].append(a.id)
            if a.role == "schueler" and a.student_id:
                self.by_student[a.student_id].append(a.id)
            if a.teacher_id:
                self.by_teacher[a.teacher_id].append(a.id)
            if a.role == "eltern":
                for sid in a.children:
                    self.parents_of[sid].append(a.id)

    def get(self, user_id: Any) -> Optional[Account]:
        try:
            return self.by_id.get(int(user_id))
        except (TypeError, ValueError):
            return None

    def reachable(self) -> list[Account]:
        return [a for a in self.by_id.values() if a.reachable]

    def students(self, student_ids: Iterable[str], routed: bool = True) -> set[int]:
        """Schülerkonten; ``routed=False`` ignoriert die Zustellwahl (Einzelnachricht an die Person)."""
        return {uid for sid in student_ids if not routed or self.routing.get(sid) != "parents"
                for uid in self.by_student.get(sid, ())}

    def parents(self, student_ids: Iterable[str]) -> set[int]:
        return {uid for sid in student_ids if self.routing.get(sid) != "self" for uid in self.parents_of.get(sid, ())}

    def teachers(self, teacher_ids: Iterable[str]) -> set[int]:
        return {uid for tid in teacher_ids for uid in self.by_teacher.get(tid, ())}

    def roles(self, roles: Iterable[str]) -> set[int]:
        return {uid for r in roles for uid in self.by_role.get(r, ())}


# --------------------------------------------------------------------------- Planungsdokument
@dataclass
class SchoolIndex:
    """Schnellzugriffe auf das Planungsdokument (einmal je Planversion aufbauen)."""
    school: School
    classes: dict[str, Any] = field(default_factory=dict)
    students: dict[str, Any] = field(default_factory=dict)
    courses: dict[str, Course] = field(default_factory=dict)
    subjects: dict[str, Any] = field(default_factory=dict)
    teachers: dict[str, Any] = field(default_factory=dict)
    sites: dict[str, Any] = field(default_factory=dict)
    students_by_class: dict[str, list[str]] = field(default_factory=dict)
    classes_by_grade: dict[int, list[str]] = field(default_factory=dict)
    class_teachers: dict[str, set[str]] = field(default_factory=dict)     # Klasse → Lehrkräfte (inkl. Klassenleitung)
    teacher_classes: dict[str, set[str]] = field(default_factory=dict)    # Lehrkraft → Klassen
    teacher_courses: dict[str, set[str]] = field(default_factory=dict)    # Lehrkraft → Kurse
    led_classes: dict[str, list[str]] = field(default_factory=dict)       # Lehrkraft → Klassen als Klassenleitung

    @classmethod
    def build(cls, school: School) -> "SchoolIndex":
        idx = cls(school=school)
        idx.classes = {c.id: c for c in school.classes}
        idx.students = {s.id: s for s in school.students}
        idx.courses = {c.id: c for c in school.courses}
        idx.subjects = {s.id: s for s in school.subjects}
        idx.teachers = {t.id: t for t in school.teachers}
        idx.sites = {s.id: s for s in school.sites}
        by_class: dict[str, list[str]] = defaultdict(list)
        for s in school.students:
            by_class[s.class_id].append(s.id)
        idx.students_by_class = dict(by_class)
        grades: dict[int, list[str]] = defaultdict(list)
        class_teachers: dict[str, set[str]] = defaultdict(set)
        teacher_classes: dict[str, set[str]] = defaultdict(set)
        teacher_courses: dict[str, set[str]] = defaultdict(set)
        led: dict[str, list[str]] = defaultdict(list)
        for c in school.classes:
            grades[c.grade].append(c.id)
            if c.class_teacher:
                class_teachers[c.id].add(c.class_teacher)
                teacher_classes[c.class_teacher].add(c.id)
                led[c.class_teacher].append(c.id)
        for course in school.courses:
            for part in course.parts:
                if part.teacher:
                    teacher_courses[part.teacher].add(course.id)
                    for cl in course.classes:
                        class_teachers[cl].add(part.teacher)
                        teacher_classes[part.teacher].add(cl)
        idx.classes_by_grade = {g: sorted(ids, key=natural_key) for g, ids in grades.items()}
        idx.class_teachers = dict(class_teachers)
        idx.teacher_classes = dict(teacher_classes)
        idx.teacher_courses = dict(teacher_courses)
        idx.led_classes = {t: sorted(ids, key=natural_key) for t, ids in led.items()}
        return idx

    # ------------------------------------------------------------------ Hilfen
    def class_name(self, class_id: str) -> str:
        c = self.classes.get(class_id)
        return (c.name or c.id) if c else class_id

    def site_name(self, site_id: str) -> str:
        s = self.sites.get(site_id)
        return (s.name or s.id) if s else site_id

    def student_class(self, student_id: Optional[str]) -> Optional[str]:
        st = self.students.get(student_id or "")
        return st.class_id if st else None

    def subject_name(self, subject_id: str) -> str:
        s = self.subjects.get(subject_id)
        return (s.name or s.id) if s else subject_id

    def course_label(self, course: Course, part: Optional[int] = None) -> str:
        """„Mathematik (5a)“, „Religion/PP 5a+5b – ev“ (Kursteil)."""
        classes = ", ".join(self.class_name(c) for c in course.classes)
        if part is not None and 0 <= part < len(course.parts):
            p = course.parts[part]
            base = course.label or self.subject_name(p.subject)
            detail = p.label or self.subject_name(p.subject)
            text = f"{base} – {detail}"
        elif len({p.subject for p in course.parts}) == 1 and course.parts:
            text = course.label or self.subject_name(course.parts[0].subject)
        else:
            text = course.label or " / ".join(dict.fromkeys(self.subject_name(p.subject) for p in course.parts))
        if not classes or all(self.class_name(c) in text for c in course.classes):
            return text
        return f"{text} ({classes})"

    def course_students(self, course: Course, part: Optional[int] = None) -> list[str]:
        """Schüler-IDs eines Kurses bzw. Kursteils – Semantik wie ``timetable.student_parts`` (ohne Wahl: alle
        Teile)."""
        multi = len(course.parts) > 1
        prefix = f"{course.id}#"
        out: list[str] = []
        for class_id in course.classes:
            for sid in self.students_by_class.get(class_id, ()):
                if not multi or part is None:
                    out.append(sid)
                    continue
                st = self.students[sid]
                chosen = {int(r[len(prefix):]) for r in st.courses
                          if r.startswith(prefix) and r[len(prefix):].isdigit()}
                for i, p in enumerate(course.parts):
                    if p.students and sid in p.students:
                        chosen.add(i)
                if not chosen or part in chosen:
                    out.append(sid)
        return out

    def classes_at_site(self, site: str) -> list[str]:
        return [c.id for c in self.school.classes if c.site == site]

    def teacher_at_site(self, teacher_id: str, site: str) -> bool:
        t = self.teachers.get(teacher_id)
        if t is None:
            return False
        return not t.sites or site in t.sites


# --------------------------------------------------------------------------- Gruppen
@dataclass(frozen=True)
class Group:
    kind: str
    ref: str
    label: str

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.ref}"

    @property
    def category(self) -> str:
        return GROUP_CATEGORY.get(self.kind, "schule")


def split_course_ref(ref: str) -> tuple[str, Optional[int]]:
    cid, sep, part = (ref or "").rpartition("#")
    if sep and part.isdigit():
        return cid, int(part)
    return ref, None


def _unknown(what: str) -> MessagingError:
    return MessagingError(f"{what} gibt es nicht (mehr).", 422, "unknown_group")


def group_label(idx: SchoolIndex, kind: str, ref: str) -> str:
    """Beschriftung einer Gruppe; :class:`MessagingError` (422) bei unbekannter Gruppe/Referenz."""
    ref = (ref or "").strip()
    if kind in CLASS_KINDS:
        if ref not in idx.classes:
            raise _unknown(f"Die Klasse „{ref}“")
        name = idx.class_name(ref)
        return {"class": f"Klasse {name} – Schüler/innen", "class_parents": f"Klasse {name} – Eltern",
                "class_lead": f"Klasse {name} – Klassenleitung",
                "class_teachers": f"Klasse {name} – Lehrkräfte"}[kind]
    if kind == "role":
        if ref not in ROLE_GROUP_ROLES:
            raise _unknown(f"Die Rolle „{ref}“")
        return f"Alle mit Rolle {ROLE_LABELS.get(ref, ref)}"
    if kind == "course":
        cid, part = split_course_ref(ref)
        course = idx.courses.get(cid)
        if course is None or (part is not None and not 0 <= part < len(course.parts)):
            raise _unknown(f"Den Kurs „{ref}“")
        if part is not None and len(course.parts) <= 1:
            part = None
        return f"Kurs {idx.course_label(course, part)} – Schüler/innen"
    if kind in ("grade", "grade_parents"):
        if not ref.isdigit() or int(ref) not in idx.classes_by_grade:
            raise _unknown(f"Den Jahrgang „{ref}“")
        return f"Jahrgang {int(ref)} – " + ("Schüler/innen" if kind == "grade" else "Eltern")
    if kind in SITE_GROUP_KINDS:
        if ref and ref not in idx.sites:
            raise _unknown(f"Den Standort „{ref}“")
        site = idx.site_name(ref) if ref else ""
        if kind == "staff":
            return f"Kollegium {site}".strip() if site else "Kollegium (alle Lehrkräfte und Verwaltung)"
        if kind == "teachers":
            return f"Nur Lehrkräfte am Standort {site}" if site else "Nur Lehrkräfte (alle)"
        if kind == "class_leads":
            return f"Klassenleitungen am Standort {site}" if site else "Alle Klassenleitungen"
        if kind == "students":
            return f"Schüler/innen am Standort {site}" if site else "Alle Schüler/innen"
        if kind == "parents":
            return f"Eltern am Standort {site}" if site else "Alle Eltern"
        return f"Standort {site} – alle Personen" if site else "Ganze Schule – alle Personen"
    raise MessagingError(f"Unbekannte Gruppenart „{kind}“.", 422, "unknown_group")


def normalize_group(idx: SchoolIndex, kind: str, ref: str) -> Group:
    """Prüft die Gruppe und normalisiert ``ref`` (Kursteil eines Ein-Teil-Kurses → ganzer Kurs)."""
    ref = (ref or "").strip()
    if kind == "course":
        cid, part = split_course_ref(ref)
        course = idx.courses.get(cid)
        if course is not None and part is not None and len(course.parts) <= 1 and part == 0:
            ref = cid
    if kind in ("grade", "grade_parents") and ref.isdigit():
        ref = str(int(ref))
    return Group(kind, ref, group_label(idx, kind, ref))


def _site_staff(idx: SchoolIndex, directory: Directory, site: str) -> set[int]:
    out: set[int] = set()
    for uid in directory.roles(COLLEGIUM_ROLES):
        acc = directory.by_id[uid]
        if acc.teacher_id and acc.teacher_id in idx.teachers:
            if idx.teacher_at_site(acc.teacher_id, site):
                out.add(uid)
        elif not acc.site or acc.site == site:
            out.add(uid)
    return out


def group_student_ids(idx: SchoolIndex, kind: str, ref: str) -> list[str]:
    """Schüler-IDs, auf die sich eine Schüler-/Elterngruppe bezieht."""
    if kind in ("class", "class_parents"):
        return list(idx.students_by_class.get(ref, ()))
    if kind == "course":
        cid, part = split_course_ref(ref)
        course = idx.courses.get(cid)
        return idx.course_students(course, part) if course else []
    if kind in ("grade", "grade_parents"):
        return [sid for cl in idx.classes_by_grade.get(int(ref) if ref.isdigit() else -1, ())
                for sid in idx.students_by_class.get(cl, ())]
    if kind in ("students", "parents", "school"):
        if not ref:
            return list(idx.students)
        return [sid for cl in idx.classes_at_site(ref) for sid in idx.students_by_class.get(cl, ())]
    return []


def group_members(idx: SchoolIndex, directory: Directory, kind: str, ref: str) -> set[int]:
    """Konto-IDs (nur erreichbare) einer Gruppe."""
    if kind in ("class", "course", "grade", "students"):
        return directory.students(group_student_ids(idx, kind, ref))
    if kind in ("class_parents", "grade_parents", "parents"):
        return directory.parents(group_student_ids(idx, kind, ref))
    if kind == "class_teachers":
        return directory.teachers(idx.class_teachers.get(ref, ()))
    if kind == "class_lead":
        lead = getattr(idx.classes.get(ref), "class_teacher", None)
        return directory.teachers([lead] if lead else [])
    if kind == "teachers":
        tids = [t for t in idx.teachers if not ref or idx.teacher_at_site(t, ref)]
        return {u for u in directory.teachers(tids) if directory.by_id[u].role == "lehrer"}
    if kind == "class_leads":
        return directory.teachers(t for t, led in idx.led_classes.items()
                                  if not ref or any(getattr(idx.classes.get(c), "site", "") == ref for c in led))
    if kind == "role":
        return directory.roles([ref]) if ref in ROLE_GROUP_ROLES else set()
    if kind == "staff":
        return _site_staff(idx, directory, ref) if ref else directory.roles(COLLEGIUM_ROLES)
    if kind == "school":
        students = group_student_ids(idx, "school", ref)
        staff = _site_staff(idx, directory, ref) if ref else directory.roles(COLLEGIUM_ROLES)
        return directory.students(students) | directory.parents(students) | staff
    return set()


def check_group(idx: SchoolIndex, sender: Any, kind: str, ref: str) -> Group:
    """Darf ``sender`` an diese Gruppe schreiben? Gibt die normalisierte Gruppe zurück, sonst :class:`MessagingError`."""
    if not has(sender, BROADCAST_PERMISSION):
        raise MessagingError("Nachrichten an Gruppen (Klassen, Kurse, Kollegium …) sind für Ihr Konto nicht "
                             "freigeschaltet – bitte einzelne Personen auswählen.", 403, "no_broadcast")
    group = normalize_group(idx, kind, ref)
    scope = perm_scope(sender, BROADCAST_PERMISSION)
    if scope is None:
        return group
    if scope == "own_classes":
        tid = getattr(sender, "teacher_id", None) or ""
        if group.kind in CLASS_KINDS:
            if group.ref in idx.teacher_classes.get(tid, ()):
                return group
            raise MessagingError(f"Die Klasse {idx.class_name(group.ref)} gehört nicht zu Ihren Klassen.", 403,
                                 "foreign_class")
        if group.kind == "course":
            cid, part = split_course_ref(group.ref)
            course = idx.courses[cid]
            taught = {i for i, p in enumerate(course.parts) if p.teacher and p.teacher == tid}
            if (part is None and taught and len(taught) == len(course.parts)) or (part is not None and part in taught):
                return group
            if part is None and taught:
                raise MessagingError("Sie unterrichten nur einen Teil dieses Kurses – bitte Ihren Kursteil "
                                     "auswählen.", 403, "foreign_course")
            raise MessagingError("Dieser Kurs gehört nicht zu Ihren Kursen.", 403, "foreign_course")
        raise MessagingError("Lehrkräfte können Rundschreiben nur an eigene Klassen und Kurse senden.", 403,
                             "teacher_scope")
    raise MessagingError("Keine Berechtigung für diese Gruppe.", 403, "forbidden")


def _candidate_groups(idx: SchoolIndex, sender: Any, *, include_all: bool) -> list[tuple[str, str]]:
    """Mögliche Gruppen ``(kind, ref)`` des Absenders (ohne Beschriftung, noch ungefiltert)."""
    if not has(sender, BROADCAST_PERMISSION):
        return []
    scope = perm_scope(sender, BROADCAST_PERMISSION)
    out: list[tuple[str, str]] = []
    if scope == "own_classes":
        tid = getattr(sender, "teacher_id", None) or ""
        for cl in sorted(idx.teacher_classes.get(tid, ()), key=natural_key):
            out += [("class", cl), ("class_parents", cl), ("class_lead", cl), ("class_teachers", cl)]
        for cid in sorted(idx.teacher_courses.get(tid, ()), key=natural_key):
            course = idx.courses[cid]
            taught = [i for i, p in enumerate(course.parts) if p.teacher == tid]
            if len(course.parts) <= 1 or len(taught) == len(course.parts):
                out.append(("course", cid))
            else:
                out += [("course", f"{cid}#{i}") for i in taught]
        return out
    if scope is not None:
        return []
    for kind in ("school", "staff", "teachers", "class_leads", "students", "parents"):
        out.append((kind, ""))
    out += [("role", r) for r in ROLE_GROUP_ROLES]
    if len(idx.sites) > 1:
        for site in sorted(idx.sites, key=natural_key):
            for kind in ("school", "staff", "teachers", "class_leads", "students", "parents"):
                out.append((kind, site))
    for grade in sorted(idx.classes_by_grade):
        out += [("grade", str(grade)), ("grade_parents", str(grade))]
    if include_all:
        for cl in sorted(idx.classes, key=natural_key):
            out += [("class", cl), ("class_parents", cl), ("class_lead", cl), ("class_teachers", cl)]
        for cid in sorted(idx.courses, key=natural_key):
            course = idx.courses[cid]
            out.append(("course", cid))
            if len(course.parts) > 1:
                out += [("course", f"{cid}#{i}") for i in range(len(course.parts))]
    return out


def allowed_groups(idx: SchoolIndex, directory: Directory, sender: Any, query: str = "", *,
                   limit: int = 40, with_counts: bool = True) -> list[dict[str, Any]]:
    """Gruppen fürs Adressbuch: ohne Suchtext die „naheliegenden“ (Lehrkraft: eigene Klassen/Kurse; Verwaltung:
    Schule, Standorte, Jahrgänge), mit Suchtext auch alle passenden Klassen und Kurse."""
    query = (query or "").strip()
    candidates = _candidate_groups(idx, sender, include_all=bool(query))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for kind, ref in candidates:
        try:
            group = normalize_group(idx, kind, ref)
        except MessagingError:
            continue
        if group.key in seen:
            continue
        if query and not matches([group.label, group.ref, CATEGORY_LABELS.get(group.category, "")], query):
            continue
        seen.add(group.key)
        item: dict[str, Any] = {"type": "group", "kind": group.kind, "ref": group.ref, "key": group.key,
                                "label": group.label, "category": group.category,
                                "category_label": CATEGORY_LABELS.get(group.category, "")}
        out.append(item)
        if len(out) >= limit:
            break
    if with_counts:
        for item in out:
            item["count"] = len(group_members(idx, directory, item["kind"], item["ref"]) - {getattr(sender, "id", 0)})
    return out


# --------------------------------------------------------------------------- Einzelpersonen
def check_direct(sender: Any, target: Optional[Account], *, students_to_students: bool, blocked: bool) -> Account:
    """Darf ``sender`` dieser Person schreiben? Gibt das Konto zurück, sonst :class:`MessagingError`."""
    if target is None or not target.reachable:
        raise MessagingError("Diese Person kann keine Nachrichten empfangen (Konto unbekannt, deaktiviert oder ohne "
                             "Postfach).", 422, "unreachable")
    if target.id == getattr(sender, "id", None):
        raise MessagingError("Sie können sich nicht selbst schreiben.", 422, "self")
    if not students_to_students and getattr(sender, "role", "") == "schueler" and target.role == "schueler":
        raise MessagingError("Nachrichten zwischen Schülerinnen und Schülern sind an dieser Schule abgeschaltet.",
                             403, "students_to_students")
    if blocked:
        raise MessagingError(f"{target.name} nimmt keine Nachrichten von Ihnen an.", 403, "blocked")
    return target


def can_block(target: Optional[Account]) -> bool:
    """Blockieren ist nur für Nicht-Personal möglich (Schulpersonal muss erreichbar bleiben → Melden)."""
    return target is not None and target.role not in STAFF_ROLES


def students_conflict(sender: Any, others: Iterable[Account], *, students_to_students: bool) -> bool:
    """True, wenn ein/e Schüler/in bei abgeschaltetem Schüler-Austausch andere Schüler/innen erreichen würde."""
    if students_to_students or getattr(sender, "role", "") != "schueler":
        return False
    return any(a.role == "schueler" and a.id != getattr(sender, "id", None) for a in others)


# --------------------------------------------------------------------------- Adressbuch
def _class_visible(idx: SchoolIndex, viewer: Any, class_id: Optional[str]) -> bool:
    """Darf der Betrachter Schüler einer Klasse über die Klasse finden bzw. Kindernamen sehen?"""
    if not class_id or not is_staff(viewer):
        return False
    scope = perm_scope(viewer, "students.read") if has(viewer, "students.read") else "none"
    if scope is None:
        return True
    if scope == "own_classes":
        return class_id in idx.teacher_classes.get(getattr(viewer, "teacher_id", None) or "", ())
    return False


def person_card(idx: SchoolIndex, viewer: Any, acc: Account) -> dict[str, Any]:
    """Darstellung einer Person für den Betrachter (datensparsam)."""
    info = ""
    if acc.role == "schueler":
        cl = idx.student_class(acc.student_id)
        info = f"Klasse {idx.class_name(cl)}" if cl else ""
    elif acc.role == "eltern":
        classes = sorted({c for c in (idx.student_class(s) for s in acc.children) if c}, key=natural_key)
        if is_staff(viewer):
            names = [f"{idx.students[s].name} ({idx.class_name(idx.students[s].class_id)})" for s in acc.children
                     if s in idx.students and _class_visible(idx, viewer, idx.students[s].class_id)]
            info = ("Eltern von " + ", ".join(names)) if names else \
                ("Klasse " + ", ".join(idx.class_name(c) for c in classes) if classes else "")
        elif classes:
            info = "Klasse " + ", ".join(idx.class_name(c) for c in classes)
    elif acc.teacher_id:
        parts = [acc.teacher_id]
        led = idx.led_classes.get(acc.teacher_id)
        if led:
            parts.append("Klassenleitung " + ", ".join(idx.class_name(c) for c in led))
        info = " · ".join(parts)
    return {"type": "user", "id": acc.id, "name": acc.name, "role": acc.role, "role_label": acc.role_label,
            "info": info}


def _viewer_classes(idx: SchoolIndex, viewer: Any) -> set[str]:
    """Klassen des Betrachters (Schüler: eigene, Eltern: der Kinder, Lehrkraft: unterrichtete)."""
    out = {idx.student_class(s) for s in (getattr(viewer, "student_ids", None) or [])}
    if getattr(viewer, "student_id", None):
        out.add(idx.student_class(viewer.student_id))
    tid = getattr(viewer, "teacher_id", None)
    if tid:
        out |= idx.teacher_classes.get(tid, set())
    return {c for c in out if c}


def search_people(idx: SchoolIndex, directory: Directory, sender: Any, query: str, *, students_to_students: bool,
                  blocked_by: set[int], limit: int = 25) -> list[dict[str, Any]]:
    """Personensuche fürs Adressbuch.

    * Mindestens ein Suchwort muss im Namen vorkommen (mind. 2 Zeichen) – keine Auflistung ganzer Klassen für
      Schüler/Eltern. Personal darf zusätzlich nach Kürzel und (sichtbaren) Klassen suchen.
    * Nicht erreichbare Konten, das eigene Konto, Konten, die den Absender blockiert haben, und – bei abgeschaltetem
      Schüler-Austausch – andere Schüler/innen (für Schüler/innen) werden nie geliefert.
    """
    tokens = query_tokens(query)
    if not tokens or sum(len(t) for t in tokens) < 2:
        return []
    staff = is_staff(sender)
    sender_id = getattr(sender, "id", None)
    hits: list[tuple[tuple, Account]] = []
    for acc in directory.by_id.values():
        if not acc.reachable or acc.id == sender_id or acc.id in blocked_by:
            continue
        if not students_to_students and getattr(sender, "role", "") == "schueler" and acc.role == "schueler":
            continue
        name = normalize(acc.name)
        name_hit = False
        ok = True
        for t in tokens:
            if t in name:
                name_hit = True
                continue
            if staff and acc.teacher_id and t == normalize(acc.teacher_id):
                name_hit = True
                continue
            if staff:
                classes: list[Optional[str]] = []
                if acc.role == "schueler":
                    classes = [idx.student_class(acc.student_id)]
                elif acc.role == "eltern":
                    classes = [idx.student_class(s) for s in acc.children]
                if any(c and t == normalize(c) and _class_visible(idx, sender, c) for c in classes):
                    name_hit = name_hit or len(tokens) == 1
                    continue
            ok = False
            break
        if not ok or not name_hit:
            continue
        starts = any(name.startswith(t) or f" {t}" in name for t in tokens)
        role_rank = 0 if acc.role in STAFF_ROLES else 1 if acc.role == "eltern" else 2
        hits.append(((0 if starts else 1, role_rank, natural_key(acc.name)), acc))
    hits.sort(key=lambda h: h[0])
    return [person_card(idx, sender, acc) for _, acc in hits[:limit]]


def find_classes(idx: SchoolIndex, query: str, limit: int = 6) -> list[dict[str, Any]]:
    """Klassen, deren Name/Kennung zum Suchtext passt (für die Klassenansicht im Adressbuch)."""
    q = normalize(query).replace(" ", "")
    if not q:
        return []
    hits = [c for c in idx.classes.values() if normalize(c.id).startswith(q) or normalize(c.name or "").replace(" ", "")
            .startswith(q)]
    hits.sort(key=lambda c: (normalize(c.id) != q, natural_key(c.id)))
    return [{"id": c.id, "name": idx.class_name(c.id)} for c in hits[:limit]]


def class_roster(idx: SchoolIndex, directory: Directory, viewer: Any, class_id: str, *, students_to_students: bool,
                 blocked_by: set[int]) -> dict[str, Any]:
    """Klassenansicht im Adressbuch: Klassenleitung und Lehrkräfte für alle; Kinder mit ihren Eltern (inkl. Geschwister
    in anderen Klassen) nur für Personal, das die Klasse sehen darf (``_class_visible``). ``groups``: Gruppen dieser
    Klasse, an die der Betrachter als Rundschreiben senden darf (sonst gehen die Knöpfe an die einzelnen Personen)."""
    if class_id not in idx.classes:
        raise _unknown(f"Die Klasse „{class_id}“")
    me = getattr(viewer, "id", None)

    def card(uid: int) -> Optional[dict[str, Any]]:
        acc = directory.by_id.get(uid)
        if acc is None or not acc.reachable or uid == me or uid in blocked_by:
            return None
        if not students_to_students and getattr(viewer, "role", "") == "schueler" and acc.role == "schueler":
            return None
        return person_card(idx, viewer, acc)

    lead = getattr(idx.classes[class_id], "class_teacher", None)
    leads = [c for c in (card(u) for u in sorted(directory.teachers([lead] if lead else []))) if c]
    lead_ids = {c["id"] for c in leads}
    teachers = sorted((c for c in (card(u) for u in directory.teachers(idx.class_teachers.get(class_id, ())))
                       if c and c["id"] not in lead_ids), key=lambda c: natural_key(c["name"]))
    full = _class_visible(idx, viewer, class_id)
    students: list[dict[str, Any]] = []
    if full:
        for sid in sorted(idx.students_by_class.get(class_id, ()), key=lambda s: natural_key(idx.students[s].name)):
            parents = []
            for uid in sorted(directory.parents([sid])):
                pc = card(uid)
                if pc is None:
                    continue
                acc = directory.by_id[uid]
                pc["children"] = [{"id": c, "name": idx.students[c].name, "class": idx.class_name(idx.students[c].class_id),
                                   "same_class": idx.students[c].class_id == class_id}
                                  for c in acc.children if c in idx.students]
                parents.append(pc)
            accounts = [c for c in (card(u) for u in sorted(directory.students([sid]))) if c]
            students.append({"student_id": sid, "name": idx.students[sid].name,
                             "account": accounts[0] if accounts else None, "parents": parents})
    groups = []
    for kind in ("class", "class_parents", "class_lead", "class_teachers"):
        try:
            g = check_group(idx, viewer, kind, class_id)
        except MessagingError:
            continue
        groups.append({"type": "group", "kind": g.kind, "ref": g.ref, "key": g.key, "label": g.label,
                       "category": g.category, "category_label": CATEGORY_LABELS.get(g.category, ""),
                       "count": len(group_members(idx, directory, g.kind, g.ref) - {me})})
    return {"class": {"id": class_id, "name": idx.class_name(class_id)}, "full": full, "leads": leads,
            "teachers": teachers, "students": students, "groups": groups}


def suggestions(idx: SchoolIndex, directory: Directory, sender: Any, *, blocked_by: set[int],
                limit: int = 12) -> list[dict[str, Any]]:
    """Vorschläge ohne Suchtext: Schüler/Eltern → Lehrkräfte der eigenen Klasse(n) und Verwaltung; Personal → keine."""
    if is_staff(sender):
        return []
    classes = _viewer_classes(idx, sender)
    teacher_ids: set[str] = set()
    for cl in classes:
        teacher_ids |= idx.class_teachers.get(cl, set())
    leaders = {t for t in teacher_ids if set(idx.led_classes.get(t, ())) & classes}
    ids = directory.teachers(teacher_ids) | directory.roles(("sekretariat", "schulleitung"))
    accounts = [directory.by_id[i] for i in ids if i != getattr(sender, "id", None) and i not in blocked_by]

    def rank(a: Account) -> tuple:
        tid = a.teacher_id or ""
        return (0 if tid in leaders else 1 if tid in teacher_ids else 2, natural_key(a.name))

    accounts.sort(key=rank)
    return [person_card(idx, sender, a) for a in accounts[:limit]]


def reply_mode(kind: str, allow_replies: str, *, is_creator: bool) -> Optional[str]:
    """Wie darf ein Teilnehmer antworten? ``"all"`` (in der Unterhaltung), ``"private"`` (eigene Unterhaltung mit dem
    Absender des Rundschreibens) oder ``None`` (keine Antworten)."""
    if is_creator or kind == "direct":
        return "all"
    if allow_replies == "all":
        return "all"
    if allow_replies == "sender":
        return "private"
    return None
