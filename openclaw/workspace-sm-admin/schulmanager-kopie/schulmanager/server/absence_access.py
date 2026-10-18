"""Wer sieht und bearbeitet welche Schüler-Krankmeldung (A-58, B-06).

Stufe eines Kontos für eine Schülerin/einen Schüler (:meth:`AbsenceAccess.level`):

* ``full``   – Sekretariat und Schulleitung (``student_absence.read`` ohne Scope) sowie die **Klassenleitung** der
  Klasse: Grund, Vermerk, Status, Attest, meldende Person; Status/Vermerk setzen, löschen, beliebig melden.
* ``family`` – die Schülerin/der Schüler selbst und die Eltern; bei Volljährigen nur mit Freigabe im Bereich
  ``krankmeldungen`` (:func:`parent_access.parent_may_see`). Alles lesen, nichts verwalten; melden laut Recht,
  eigene Meldung zurückziehen, solange sie „gemeldet“ ist.
* ``teacher`` – Fachlehrkraft, die die Person in einem **tatsächlichen Kursteil** unterrichtet (nicht über
  ``course.classes``): liest nichts (Schulschalter ``subject_teacher_absence_view = "presence"``: „fehlt heute in
  meiner Stunde“ – Name und Stunde, ohne Status, Attest, Grund und meldende Person), meldet für die eigene Stunde
  (ein Tag, nicht in der Zukunft, nur Stunden, in denen sie die Person an diesem Tag unterrichtet – auch als
  Vertretung) und löscht die eigene Meldung, solange sie „gemeldet“ ist.
* ``None``   – keine Beziehung: fremde Daten → 404.

Die technische Administration hat kein ``student_absence.read`` (Datensparsamkeit) und fällt damit heraus.
Die Klasse wertet nur ``lehrer``-Konten über ``teacher_id`` aus (U-26: ``teacher_id`` an anderen Rollen zählt nicht).
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Optional

FULL, FAMILY, TEACHER = "full", "family", "teacher"
VIEW_NONE, VIEW_PRESENCE = "none", "presence"
SUBJECT_VIEWS = (VIEW_NONE, VIEW_PRESENCE)
FAMILY_ROLES = frozenset({"schueler", "eltern"})
READ, REPORT = "student_absence.read", "student_absence.report"


def subject_view(school: Any) -> str:
    """Schulschalter ``subject_teacher_absence_view`` (unbekannte Werte zählen als ``none``)."""
    value = getattr(getattr(school, "settings", None), "subject_teacher_absence_view", VIEW_NONE)
    return value if value in SUBJECT_VIEWS else VIEW_NONE


# ----------------------------------------------------------------------------- Kursteile → Schüler/innen
def part_members(school: Any, course: Any) -> list[frozenset[str]]:
    """Schüler-IDs je Kursteil – dieselbe Regel wie ``timetable.student_parts``: Ein-Teil-Kurs = ganze Klasse(n);
    bei mehreren Teilen die Wahl (``Student.courses`` „kurs#teil“ bzw. ``CoursePart.students``), ohne Wahl alle."""
    parts = list(course.parts or [])
    if not parts:
        return []
    classes = set(course.classes or [])
    studs = [s for s in school.students if s.class_id in classes]
    if len(parts) == 1:
        return [frozenset(s.id for s in studs)]
    listed = [set(p.students or []) for p in parts]
    out: list[set[str]] = [set() for _ in parts]
    prefix = f"{course.id}#"
    for s in studs:
        sel = {int(ref[len(prefix):]) for ref in (s.courses or [])
               if ref.startswith(prefix) and ref[len(prefix):].isdigit()}
        sel.update(i for i, members in enumerate(listed) if s.id in members)
        sel = {i for i in sel if 0 <= i < len(parts)} or set(range(len(parts)))
        for i in sel:
            out[i].add(s.id)
    return [frozenset(x) for x in out]


def taught_students(school: Any, teacher_id: Optional[str]) -> frozenset[str]:
    """Schüler/innen, die einen Kursteil der Lehrkraft tatsächlich besuchen (ohne Klassenleitung)."""
    if not teacher_id:
        return frozenset()
    out: set[str] = set()
    for course in school.courses:
        idx = [i for i, p in enumerate(course.parts or []) if p.teacher == teacher_id]
        if not idx:
            continue
        members = part_members(school, course)
        for i in idx:
            if i < len(members):
                out |= members[i]
    return frozenset(out)


def class_teacher_students(school: Any, teacher_id: Optional[str]) -> frozenset[str]:
    """Schüler/innen der Klassen, deren Klassenleitung die Lehrkraft ist."""
    if not teacher_id:
        return frozenset()
    classes = {c.id for c in school.classes if c.class_teacher == teacher_id}
    return frozenset(s.id for s in school.students if s.class_id in classes)


def _cached(kind: str, key: tuple, compute, snap):
    from .routes.features_common import cached

    return cached(kind, key, compute, snap)


def lesson_periods(snap: Any, teacher_id: str, day: date) -> dict[str, set[int]]:
    """Schüler-ID → Stunden am ``day``, in denen die Lehrkraft sie unterrichtet (effektiver Tag: Vertretungen und
    Entfall berücksichtigt, Aufsichten nicht)."""
    def compute() -> dict[str, frozenset[int]]:
        from .routes.features_common import effective_cells

        school = snap[1]
        courses = school.index("courses")
        by_class: dict[str, list[str]] = {}
        for s in school.students:
            by_class.setdefault(s.class_id, []).append(s.id)
        out: dict[str, set[int]] = {}
        for cell in effective_cells(day, "teacher", teacher_id, snap):
            if cell.get("kind") == "aufsicht" or cell.get("status") == "entfall" or cell.get("dropped"):
                continue
            period = cell.get("period")
            if not isinstance(period, int):
                continue
            course = courses.get(cell.get("course_id") or "")
            if course is not None:
                members = _cached("absence_parts", (course.id,), lambda c=course: part_members(school, c), snap)
                part = int(cell.get("part") or 0)
                ids: Iterable[str] = members[part] if part < len(members) else ()
                classes = set(cell.get("classes") or [])
                if classes:
                    ids = [sid for sid in ids if school.index("students")[sid].class_id in classes]
            else:
                ids = [sid for cls in cell.get("classes") or [] for sid in by_class.get(cls, [])]
            for sid in ids:
                out.setdefault(sid, set()).add(period)
        return {sid: frozenset(p) for sid, p in out.items()}

    return _cached("absence_lesson_periods", (teacher_id, day.isoformat()), compute, snap)


# ----------------------------------------------------------------------------- Zugriff je Anfrage
class AbsenceAccess:
    """Rechte und Datenumfang eines Kontos für Krankmeldungen (je Anfrage, Planungsstand ``snap``)."""

    def __init__(self, user: Any, snap: Any, db: Any):
        from .routes.features_common import has, own_student_ids, perm_scope

        self.user, self.snap, self.db, self.school = user, snap, db, snap[1]
        self.uid = getattr(user, "id", None) or None
        self.role = getattr(user, "role", "")
        self.can_read = has(user, READ)
        self.staff_all = (self.role not in FAMILY_ROLES and self.can_read
                          and perm_scope(user, READ) is None)
        self.teacher_id = getattr(user, "teacher_id", None) if self.role == "lehrer" else None
        self._own_ids = own_student_ids(user) if self.role in FAMILY_ROLES else []
        self._family: Optional[frozenset[str]] = None
        # Volljährig nach Geburtsdatum (``parent_access.is_adult``) meldet sich selbst – auch ohne Konto-Merkmal
        # ``users.adult``; sonst sperrt die Elternfreigabe die Eltern aus und niemand in der Familie kann melden
        # Schüler/innen melden sich nur selbst krank, wenn sie volljährig sind – ein Recht allein (z. B. veraltetes
        # Konto-Merkmal ``users.adult`` bei Geburtsdatum unter 18) genügt nie; Minderjährige meldet die Familie.
        self.can_report = self._adult_pupil() if self.role == "schueler" else has(user, REPORT)

    def _adult_pupil(self) -> bool:
        if self.role != "schueler" or len(self._own_ids) != 1 or self.db is None:
            return False
        from . import parent_access as pa

        return pa.is_adult(self.db, self._own_ids[0], school=self.school)

    # --- Beziehungen
    @property
    def family_ids(self) -> frozenset[str]:
        """Eigene Person bzw. Kinder, deren Krankmeldungen das Konto sehen darf (Elternfreigabe bei Volljährigen)."""
        if self._family is None:
            if self.role == "eltern":
                from . import parent_access as pa

                self._family = frozenset(pa.visible_children(self.db, self._own_ids, pa.AREA_SICK_NOTES,
                                                             school=self.school))
            else:
                self._family = frozenset(self._own_ids)
        return self._family

    def linked_but_hidden(self, sid: str) -> bool:
        """Eltern eines volljährigen Kindes ohne Freigabe (verknüpft, aber kein Zugriff)."""
        return self.role == "eltern" and sid in self._own_ids and sid not in self.family_ids

    @property
    def class_students(self) -> frozenset[str]:
        tid = self.teacher_id
        if not tid:
            return frozenset()
        return _cached("absence_class_teacher", (tid,), lambda: class_teacher_students(self.school, tid), self.snap)

    @property
    def taught(self) -> frozenset[str]:
        tid = self.teacher_id
        if not tid:
            return frozenset()
        return _cached("absence_taught", (tid,), lambda: taught_students(self.school, tid), self.snap)

    def level(self, sid: str) -> Optional[str]:
        """``full`` | ``family`` | ``teacher`` | ``None`` (siehe Moduldoku)."""
        if self.role in FAMILY_ROLES:
            return FAMILY if (self.can_read or self.can_report) and sid in self.family_ids else None
        if self.staff_all:
            return FULL
        if self.teacher_id and (self.can_read or self.can_report):
            if sid in self.class_students:
                return FULL
            if sid in self.taught:
                return TEACHER
        return None

    def own(self, row: Any) -> bool:
        return row.reported_by is not None and row.reported_by == self.uid

    def visible_level(self, row: Any) -> Optional[str]:
        """Stufe für eine vorhandene Meldung; eine eigene Meldung einer Lehrkraft bleibt für sie sichtbar."""
        lvl = self.level(row.student_id)
        if lvl is None and self.role not in FAMILY_ROLES and self.own(row):
            return TEACHER
        return lvl

    def can_manage(self, row: Any) -> bool:
        """Status und Vermerk setzen: nur Klassenleitung, Sekretariat, Schulleitung."""
        return self.level(row.student_id) == FULL

    def can_delete(self, row: Any) -> bool:
        if self.can_manage(row):
            return True
        return self.own(row) and row.status == "gemeldet" and self.visible_level(row) is not None

    # --- Fachlehrkraft
    @property
    def presence_enabled(self) -> bool:
        return bool(self.teacher_id) and self.can_read and subject_view(self.school) == VIEW_PRESENCE

    def lesson_periods(self, day: date) -> dict[str, frozenset[int]]:
        if not self.teacher_id:
            return {}
        return lesson_periods(self.snap, self.teacher_id, day)
