"""Neutrales Austauschmodell für Importe aus Fremdsystemen (Moodle, OneRoster, WebUntis, IServ, SchILD …).

Jeder Leser (``moodle_db``, ``moodle_mbz``, ``oneroster``, ``webuntis``, ``iserv``) liefert ein :class:`Bundle`; die
Anwendungsschicht (``schulmanager/server/import_fremd.py``) kennt nur dieses Modell. So kommt ein neues Quellformat mit
einem Leser aus, ohne die Anwendungslogik anzufassen.

Konventionen
------------
* ``src_id`` ist immer ein **String** und innerhalb des Quellsystems eindeutig (Moodle: Zeilen-ID, OneRoster: ``sourcedId``).
  Aus ``(system, instance, art, src_id)`` entsteht der stabile Schlüssel für die Idempotenz.
* Texte sind Markdown/Klartext (HTML wird beim Lesen umgewandelt), Zeitpunkte ``datetime`` in UTC (naiv) oder ISO-Datum.
* Punkte sind ``float``; ``None`` heißt „nicht bewertet“ (Moodle ``-1`` wird schon im Leser zu ``None``).
* Der Leser meldet Fehlerhaftes in ``Bundle.problems`` und liest weiter (Fehlertoleranz), statt abzubrechen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class FPerson:
    src_id: str
    first: str = ""
    last: str = ""
    role: str = "student"            # student | teacher | other
    email: str = ""
    username: str = ""
    ident: str = ""                  # Kennung aus dem Quellsystem (Moodle idnumber, OneRoster identifier, Untis-ID)
    birth: str = ""                  # ISO-Datum oder leer
    class_hint: str = ""             # Klasse laut Quelle (Kohorte, Stammklasse …)
    status: str = "active"           # active | suspended | deleted
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return " ".join(x for x in (self.first, self.last) if x)


@dataclass
class FCourse:
    src_id: str
    short: str = ""
    full: str = ""
    ident: str = ""                  # idnumber / sourcedId-Kürzel
    category: str = ""
    start: str = ""
    end: str = ""
    hidden: bool = False
    summary: str = ""
    kind: str = "course"             # course | homeroom (OneRoster-Klasse vom Typ homeroom) | catalog
    grade: str = ""
    subject: str = ""
    sections: dict[int, str] = field(default_factory=dict)    # Abschnittsnummer → Name
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def title(self) -> str:
        return self.full or self.short or f"Kurs {self.src_id}"


@dataclass
class FEnrol:
    course: str
    person: str
    role: str = "student"            # student | teacher | assistant
    active: bool = True
    note: str = ""                   # z. B. „abgelaufen“, „ausgesetzt“


@dataclass
class FGroup:
    src_id: str
    course: str
    name: str
    members: list[str] = field(default_factory=list)          # Personen-src_ids
    grouping: str = ""


@dataclass
class FFile:
    src_id: str
    name: str
    mime: str = ""
    size: int = 0
    course: str = ""
    area: str = ""                   # Moodle: component/filearea
    owner: str = ""                  # Personen-src_id
    item: str = ""                   # Aufgabe/Abgabe, an der die Datei hängt (src_id)
    data: Optional[bytes] = None     # nur bei Quellen mit Dateiinhalt (.mbz)


@dataclass
class FSubmission:
    person: str
    status: str = "abgegeben"        # abgegeben | entwurf | bewertet
    text: str = ""
    at: Optional[datetime] = None
    attempt: int = 1
    points: Optional[float] = None
    max_points: Optional[float] = None
    feedback: str = ""
    graded_at: Optional[datetime] = None
    rubric_fill: dict[str, Any] = field(default_factory=dict)   # {kriterium-src_id: {"level": level-src_id, "comment": …}}
    files: list[FFile] = field(default_factory=list)
    group: str = ""                  # Gruppen-src_id bei Gruppenabgabe


@dataclass
class FAssign:
    src_id: str
    course: str
    title: str
    intro: str = ""
    due: Optional[datetime] = None
    cutoff: Optional[datetime] = None
    max_points: Optional[float] = None
    section: int = 0
    visible: bool = True
    team: bool = False
    no_submission: bool = False
    rubric: Optional[dict[str, Any]] = None                     # Ausgabe von ``grading.normalize_rubric`` + ``src_ids``
    submissions: list[FSubmission] = field(default_factory=list)
    skipped_attempts: int = 0


@dataclass
class FGradeItem:
    src_id: str
    course: str
    title: str
    kind: str = "manual"             # assign | quiz | manual | scale | other
    max_points: Optional[float] = None
    scale: list[str] = field(default_factory=list)              # Beschriftungen aufsteigend (Moodle-Skala)
    results: dict[str, tuple[Optional[float], str]] = field(default_factory=dict)   # Person → (Punkte, Notentext)
    date: str = ""
    link: str = ""                   # src_id der Aufgabe/des Quiz, aus der die Leistung stammt
    category: str = ""


@dataclass
class FQuestion:
    src_id: str
    course: str
    qtype: str                       # Typ im Quellsystem
    title: str = ""
    data: Optional[dict[str, Any]] = None   # Rohform für ``learning.normalize_question``; None = nicht übersetzbar
    reason: str = ""                 # warum nicht übersetzbar


@dataclass
class FQuiz:
    src_id: str
    course: str
    title: str
    intro: str = ""
    questions: list[str] = field(default_factory=list)
    time_limit_min: Optional[int] = None
    max_attempts: Optional[int] = None
    opens: Optional[datetime] = None
    closes: Optional[datetime] = None
    section: int = 0
    visible: bool = True


@dataclass
class FFramework:
    src_id: str
    name: str
    description: str = ""
    levels: list[str] = field(default_factory=list)
    support_level: int = 1
    areas: list[dict[str, Any]] = field(default_factory=list)   # [{name, competencies:[{src_id, code, title, descriptors}]}]
    courses: list[str] = field(default_factory=list)
    assessments: list[tuple[str, str, int, str, str]] = field(default_factory=list)   # Person, Kompetenz-src_id, Stufe, Datum, Notiz


@dataclass
class FBadge:
    src_id: str
    name: str
    description: str = ""
    course: str = ""
    active: bool = True
    awards: list[tuple[str, str]] = field(default_factory=list)     # Person, Datum


@dataclass
class FPost:
    src_id: str
    course: str
    forum: str
    subject: str
    body: str
    author: str                      # Anzeigename
    at: Optional[datetime] = None
    parent: str = ""


@dataclass
class Problem:
    kind: str                        # zeile | referenz | format | nicht_unterstuetzt | konflikt
    ref: str
    message: str


@dataclass
class Bundle:
    system: str                      # moodle | oneroster | webuntis | iserv | schild | asv
    source: str = ""                 # Dateiname/Beschreibung
    instance: str = "standard"       # Schlüssel der Quellinstanz (Idempotenz)
    version: str = ""
    persons: dict[str, FPerson] = field(default_factory=dict)
    courses: dict[str, FCourse] = field(default_factory=dict)
    enrols: list[FEnrol] = field(default_factory=list)
    groups: list[FGroup] = field(default_factory=list)
    assigns: list[FAssign] = field(default_factory=list)
    grade_items: list[FGradeItem] = field(default_factory=list)
    questions: dict[str, FQuestion] = field(default_factory=dict)
    quizzes: list[FQuiz] = field(default_factory=list)
    frameworks: list[FFramework] = field(default_factory=list)
    badges: list[FBadge] = field(default_factory=list)
    posts: list[FPost] = field(default_factory=list)
    files: list[FFile] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)   # Stammdaten: [{id, name, grade}] (Klassen/Jahrgänge)
    subjects: list[dict[str, Any]] = field(default_factory=list)   # Stammdaten: [{id, name}]
    rooms: list[dict[str, Any]] = field(default_factory=list)      # Stammdaten: [{id, name}]
    problems: list[Problem] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)

    def problem(self, kind: str, ref: str, message: str) -> None:
        self.problems.append(Problem(kind, str(ref), message))

    def counts(self) -> dict[str, int]:
        return {"persons": len(self.persons), "courses": len(self.courses), "enrols": len(self.enrols),
                "groups": len(self.groups), "assigns": len(self.assigns),
                "submissions": sum(len(a.submissions) for a in self.assigns), "grade_items": len(self.grade_items),
                "questions": len(self.questions), "quizzes": len(self.quizzes), "frameworks": len(self.frameworks),
                "badges": len(self.badges), "posts": len(self.posts), "files": len(self.files),
                "classes": len(self.classes), "subjects": len(self.subjects), "rooms": len(self.rooms)}
