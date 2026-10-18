"""Kursräume (ARCHITECTURE.md §9.4) – Kanäle je Kursteil und Klasse mit Ordnern, Material, Freigabe zur
Unterrichtsstunde, Aufgaben mit Abgabe und Rückmeldung, Pinnwand und Teilnehmenden.

Eigene Umsetzung der Moodle-Konzepte (Kurs → Abschnitte/Ordner, Material, Verfügbarkeit, Aufgaben, Forum,
Teilnehmerliste) – **kein Moodle-Code**.

Rollen im Kanal (bei jedem Zugriff dynamisch aus Planungsdokument + Konto, Logik in ``schulmanager/channels.py``):

* ``teacher`` – Lehrkraft des Kursteils bzw. der Klasse (Klassenleitung + alle Lehrkräfte mit Unterricht in der
  Klasse) mit ``channels.manage`` oder Zusatzmitglied „Lehrende“. Verwaltet Ordner, Material, Freigaben, Aufgaben,
  Abgaben und moderiert die Pinnwand. Lehrkräfte (Scope ``own_courses``) verwalten so nur ihre eigenen Kanäle.
  **Klassenräume**: fremdes Material/fremde Ordner ändern, verbergen, löschen nur Ersteller/in, Klassenleitung und
  Kursraum-Verwaltung (Zusatz-Lehrende); Abgaben und Rückmeldungen sieht nur die Lehrkraft, die die Aufgabe gestellt
  hat (:attr:`Ctx.manages_all`, :meth:`Ctx.may_edit`, :meth:`Ctx.responsible`).
* ``student`` – Schüler/in des Kursteils (laut ``timetable.student_parts``) bzw. der Klasse oder Zusatzmitglied:
  sieht nur freigegebenes Material, nur die eigenen Abgaben und die Pinnwand.
* ``supervisor`` – Schulleitung/Admin (``channels.manage`` ohne Einschränkung) ohne Mitgliedschaft: **nur lesen**
  (Material inkl. verborgener mit Status, Pinnwand, Teilnehmende, Zahl der Abgaben) – keine Abgabe-Inhalte, keine
  Noten, keine Änderungen. Wer eingreifen muss (z. B. Pinnwand moderieren), trägt sich als Zusatz-Lehrkraft ein
  (``POST /channels/{id}/members``, protokolliert). Archivieren und eigene Kanäle sind Aufgaben der Aufsicht.

* ``parent`` – Eltern (``channels.view_children``) eines Kindes, das Teilnehmende/r ist: **nur lesen** – freigegebenes
  Material, Aufgaben mit Status/Rückmeldung des eigenen Kindes, Pinnwand; keine Teilnehmenden, keine Abgaben anderer.
  Bei volljährigen Kindern nur mit deren Einwilligung (``parent_access.parent_may_see(…, "kursraeume")``). Das Kind
  wählt ``?student_id=`` (sonst das erste passende).

Mitglieder: Lehrende eines Kursraums (Fach-/Klassenlehrkräfte) tragen Schüler/innen ein und aus, die Aufsicht
(Schulleitung/Admin) zusätzlich Lehrende. Schüler/innen aus dem Stundenplan lassen sich austragen (Zusatzzeile mit Rolle
``excluded``, wieder eintragen = Zeile löschen); ausgetragene sehen den Kursraum nicht mehr, ihre Eltern auch nicht.
Wer einen eigenen Kursraum erstellt hat, kann ihn nicht verlassen und nicht ausgetragen werden (kein Aussperren).
ZIP-Download und Archivieren gibt es nicht (mehr). Material kann „Unterrichtsmaterial“ einer Stunde sein (Bereich
„Unterricht“: ``GET /channels/{id}/unterricht``) und „Abgabe möglich“ haben (Abgaben wie bei Aufgaben).

Planung, Sekretariat und Monitor haben kein ``channels.use``.

Datenschutz: Freitexte (Textseiten, Aufgabentexte, Abgaben, Rückmeldungen, Noten, Pinnwand) liegen nur
verschlüsselt in der Datenbank (``crypto``, AAD ``<tabelle>.<feld>:<id>``), Dateien verschlüsselt über ``files``
(Zugriff über ``files.register_access_check`` für ``channel_item``, ``submission``, ``channel_post``). Audit-Einträge
enthalten nie Inhalte. Live-Ereignisse ``change`` mit ``scope: ["channels", "channel:<id>:"]`` gehen nur an die
Mitglieder (ohne Inhalt).
"""
from __future__ import annotations

import io
import logging
import uuid
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import zipfile
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, defer

from schulmanager import channels as logic
from schulmanager.calendar_utils import is_school_day
from schulmanager.server import assignment_tools as at
from schulmanager.server import channel_groups as cgroups
from schulmanager.server import crypto, files, progress
from schulmanager.server import parent_access as pa
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import ParentLink, User
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.events import bus
from schulmanager.server.feature_models.channels import (AssignmentSubmission, Channel, ChannelExtraMember,
                                                         ChannelFolder, ChannelItem, ChannelItemView, ChannelPost,
                                                         ChannelRead)
from schulmanager.server.permissions import permissions_for

from .features_common import day_plan, has, parse_date, perm_scope, snapshot

log = logging.getLogger("schulmanager.channels")
router = APIRouter(tags=["Kursräume"])

TEACHER, STUDENT, SUPERVISOR, PARENT = "teacher", "student", "supervisor", "parent"
EXCLUDED = "excluded"      # Schüler/in aus dem Stundenplan wurde aus dem Kursraum ausgetragen
ROLE_LABELS = {TEACHER: "Lehrende", STUDENT: "Teilnehmende", SUPERVISOR: "Aufsicht (nur lesen)",
               PARENT: "Eltern (nur lesen)", EXCLUDED: "ausgetragen"}
NO_TEACHER_LINK = ("Ihr Konto ist keiner Lehrkraft zugeordnet – bitte wenden Sie sich an das Sekretariat oder die "
                   "Schulleitung.")
FOREIGN_MATERIAL = ("Dieses Material hat eine andere Lehrkraft eingestellt – ändern dürfen es nur sie, die "
                    "Klassenleitung und die Kursraum-Verwaltung")
KIND_LABELS = {logic.COURSE: "Kurs", logic.CLASS: "Klasse", logic.CUSTOM: "Eigener Kursraum"}
TYPE_LABELS = {"file": "Datei", "link": "Link", "text": "Textseite", "assignment": "Aufgabe"}
STATE_LABELS = {"visible": "sichtbar", "hidden": "verborgen", "scheduled": "geplant", "lesson": "zur Stunde",
                "folder_hidden": "Ordner nicht freigegeben"}
REF_ITEM, REF_SUBMISSION, REF_POST = "channel_item", "submission", "channel_post"
PURPOSE_MATERIAL, PURPOSE_SUBMISSION, PURPOSE_POST = "channel_material", "submission", "channel_post"

MAX_FOLDERS = 300            # Ordner je Kanal
MAX_FOLDER_DEPTH = 6         # Verschachtelungstiefe
MAX_ITEMS = 3000             # Materialien/Aufgaben je Kanal
MAX_BODY = 100_000           # Zeichen einer Textseite/Aufgabenbeschreibung
MAX_SUBMISSION_TEXT = 50_000
MAX_POST = 10_000
MAX_FEEDBACK = 20_000
MAX_GRADE = 30
MAX_ATTACHMENTS = 20
MAX_POST_ATTACHMENTS = 10
MAX_UPLOAD_ITEMS = 50        # Dateien je Mehrfach-Upload
MAX_TREE_PATHS = MAX_FOLDERS  # Ordner je Ordner-Upload
# Entfall/schulfrei-Verschiebung für Stunden der letzten 8 Wochen neu berechnen (= Suchfenster der Ersatzstunde,
# damit lange Ferien die Freigabe nicht vorzeitig auf den alten Stundenbeginn zurückfallen lassen)
SHIFT_LOOKBACK_DAYS = logic.MAX_UPCOMING_DAYS
MAX_COPY = 300               # Materialien je Kopiervorgang
ZIP_MAX_BYTES = 300 * 1024 * 1024
ZIP_MAX_FILES = 1000
NEW_DAYS = 14                # ohne Besuch gilt Material der letzten 14 Tage als neu
POST_RATE = (30, 10)         # höchstens 30 Beiträge in 10 Minuten je Konto
OPEN_SUBMISSIONS = ("abgegeben", "verspaetet")
_CHUNK = 500
_STORED_KINDS = frozenset({"pdf", "png", "jpeg", "gif", "webp", "heic", "docx", "xlsx", "pptx", "odt", "ods", "odp",
                           "mp3", "m4a", "ogg", "mp4", "mov", "webm", "zip"})

Visibility = Literal["visible", "hidden", "scheduled", "lesson", "next_lesson"]   # next_lesson nur als Eingabe
ItemType = Literal["file", "link", "text", "assignment"]


# =========================================================================== Eingaben (Pydantic)
class LessonRef(BaseModel):
    """Unterrichtsstunde für die Freigabe „zur Stunde“ (``period`` = geplanter Beginn, 0-basiert)."""
    model_config = ConfigDict(extra="forbid")
    date: date
    lesson_id: str = Field(min_length=1, max_length=40)
    period: int = Field(ge=0, le=15)


class ChannelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    students_can_post: bool = True
    students_can_reply: bool = True


class ChannelPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    students_can_post: Optional[bool] = None
    students_can_reply: Optional[bool] = None
    progress_parents: Optional[bool] = None       # Eltern sehen den Lernfortschritt ihres Kindes
    archived: Optional[bool] = None


class MembersIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_ids: list[int] = Field(min_length=1, max_length=500)
    role: Literal["teacher", "student"] = "student"


class FolderIn(BaseModel):
    """``hidden`` (alt) oder ``visibility`` (wie beim Material, auch zur Stunde/ab Zeitpunkt)."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    parent_id: Optional[int] = None
    hidden: bool = False
    visibility: Optional[Visibility] = None
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None


class FolderPatch(BaseModel):
    """Felder optional; ``parent_id: null`` verschiebt in die oberste Ebene (nur wenn angegeben)."""
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    parent_id: Optional[int] = None
    position: Optional[int] = Field(None, ge=0, le=1_000_000)
    hidden: Optional[bool] = None
    visibility: Optional[Visibility] = None
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None


class FolderTreeIn(BaseModel):
    """Ordner-Upload: relative Ordnerpfade (``"Projekt/Bilder"``) unter ``parent_id``; die obersten Ordner werden
    neu angelegt (Name bei Bedarf „Projekt (2)“) und bekommen die Sichtbarkeit, darunter ist alles sichtbar."""
    model_config = ConfigDict(extra="forbid")
    parent_id: Optional[int] = None
    paths: list[str] = Field(min_length=1, max_length=MAX_TREE_PATHS)
    visibility: Visibility = "visible"
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None


class ReorderIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parent_id: Optional[int] = None
    folder_ids: list[int] = Field(default_factory=list, max_length=MAX_FOLDERS)
    item_ids: list[int] = Field(default_factory=list, max_length=MAX_ITEMS)


class ItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: ItemType
    title: str = Field("", max_length=200)
    folder_id: Optional[int] = None
    body: str = Field("", max_length=MAX_BODY)
    url: Optional[str] = Field(None, max_length=2000)
    file_id: Optional[str] = Field(None, max_length=36)
    attachment_ids: list[str] = Field(default_factory=list, max_length=MAX_ATTACHMENTS)
    visibility: Visibility = "visible"
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None
    due_at: Optional[datetime] = None
    allow_late: bool = True
    lesson_material: bool = False
    material_date: Optional[date] = None
    submittable: bool = False
    info_card: bool = False          # nur Klassenräume: angeheftete Infokarte (Textseite im Bereich „Klasse“)


class ItemPatch(BaseModel):
    """Felder optional; ``folder_id``/``due_at`` mit ``null`` = in die oberste Ebene / Frist entfernen."""
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(None, max_length=200)
    folder_id: Optional[int] = None
    body: Optional[str] = Field(None, max_length=MAX_BODY)
    url: Optional[str] = Field(None, max_length=2000)
    file_id: Optional[str] = Field(None, max_length=36)
    attachment_ids: Optional[list[str]] = Field(None, max_length=MAX_ATTACHMENTS)
    visibility: Optional[Visibility] = None
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None
    due_at: Optional[datetime] = None
    allow_late: Optional[bool] = None
    position: Optional[int] = Field(None, ge=0, le=1_000_000)
    lesson_material: Optional[bool] = None
    material_date: Optional[date] = None
    submittable: Optional[bool] = None


class FilesIn(BaseModel):
    """Mehrfach-Upload: je Datei ein Material im Ordner (gleiche Sichtbarkeit für alle)."""
    model_config = ConfigDict(extra="forbid")
    folder_id: Optional[int] = None
    file_ids: list[str] = Field(min_length=1, max_length=MAX_UPLOAD_ITEMS)
    visibility: Visibility = "visible"
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None
    lesson_material: bool = False
    material_date: Optional[date] = None
    submittable: bool = False


class VisibilityIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_ids: list[int] = Field(default_factory=list, max_length=200)
    folder_ids: list[int] = Field(default_factory=list, max_length=MAX_FOLDERS)
    visibility: Visibility
    visible_from: Optional[datetime] = None
    lesson: Optional[LessonRef] = None


class CopyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_channel_id: int
    target_folder_id: Optional[int] = None
    item_ids: list[int] = Field(default_factory=list, max_length=MAX_COPY)
    folder_ids: list[int] = Field(default_factory=list, max_length=50)
    keep_visibility: bool = False


class PostIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=MAX_POST)
    parent_id: Optional[int] = None
    attachment_ids: list[str] = Field(default_factory=list, max_length=MAX_POST_ATTACHMENTS)


class PostPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: Optional[str] = Field(None, min_length=1, max_length=MAX_POST)
    pinned: Optional[bool] = None


# =========================================================================== Hilfen
def _chunks(values: Iterable[Any], size: int = _CHUNK) -> Iterator[list[Any]]:
    vals = list(values)
    for i in range(0, len(vals), size):
        yield vals[i:i + size]


def _to_utc(value: Optional[datetime], what: str) -> Optional[datetime]:
    """Eingabe-Zeitpunkt → naive UTC (ohne Zeitzone = Ortszeit des Servers)."""
    if value is None:
        return None
    dt = value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else logic.local_to_utc(value)
    if not 2000 <= dt.year <= 2100:
        raise HTTPException(422, f"Ungültiger Zeitpunkt für {what}")
    return dt.replace(microsecond=0)


def _is_supervisor(user: AuthUser) -> bool:
    """Schulleitung/Admin: ``channels.manage`` ohne Einschränkung."""
    return has(user, "channels.manage") and perm_scope(user, "channels.manage") is None


def _uses_channels(user: AuthUser) -> bool:
    return has(user, "channels.use") or has(user, "channels.manage")


def _is_parent(user: Any) -> bool:
    """Elternkonto mit Lesezugriff auf die Kursräume der Kinder (``channels.view_children``)."""
    return has(user, "channels.view_children") and getattr(user, "role", "") == "eltern"


def _need_channels(user: AuthUser) -> None:
    if not (_uses_channels(user) or _is_parent(user)):
        raise HTTPException(403, "Keine Berechtigung für Kursräume")


def _no_teacher_link(user: Any) -> bool:
    """Lehrkraft-Konto ohne Zuordnung zu einer Lehrkraft des Planungsdokuments (keine Kursräume)."""
    return getattr(user, "role", "") == "lehrer" and not getattr(user, "teacher_id", None)


def _account_of(db: Session, student_id: Optional[str]) -> Optional[int]:
    """Aktives Schülerkonto zu einer Schüler-ID (für Abgaben/Status in der Elternansicht)."""
    if not student_id:
        return None
    return db.scalars(select(User.id).where(User.student_id == student_id, User.role == "schueler",
                                            User.active.is_(True)).order_by(User.id)).first()


def _spec_for(school, ch: Channel) -> Optional[logic.ChannelSpec]:
    if ch.kind in (logic.COURSE, logic.CLASS) and ch.ref:
        return logic.channel_spec(school, ch.kind, ch.ref)
    return None


_NO_EXTRA = object()


def _parent_children(db: Session, user: Any, ch: Channel, spec: Optional[logic.ChannelSpec], school) -> list[str]:
    """Kinder eines Elternkontos, die Teilnehmende des Kanals sind und deren Kursräume die Eltern sehen dürfen
    (minderjährig immer, volljährig nur mit Einwilligung)."""
    out: list[str] = []
    for kid in dict.fromkeys(getattr(user, "student_ids", None) or []):
        uid = _account_of(db, kid)
        extra = db.scalar(select(ChannelExtraMember.role).where(
            ChannelExtraMember.channel_id == ch.id, ChannelExtraMember.user_id == uid)) if uid is not None else None
        if extra == EXCLUDED:
            continue                      # aus dem Kursraum ausgetragen: auch die Eltern nicht mehr
        member = extra in (TEACHER, STUDENT) or (
            spec is not None and logic.is_channel_student(school, ch.kind, ch.ref or "", kid))
        if member and pa.parent_may_see(db, kid, pa.AREA_CHANNELS, school=school):
            out.append(kid)
    return out


def _access(db: Session, user: Any, ch: Channel, spec: Optional[logic.ChannelSpec], school,
            extra: Any = _NO_EXTRA) -> tuple[Optional[str], Optional[str], list[str]]:
    """``(Rolle, Zusatzmitglied-Rolle, Kinder)``: ``teacher`` > ``student`` > ``supervisor``; Eltern ``parent``."""
    manage = has(user, "channels.manage")
    if not (manage or has(user, "channels.use")):
        if _is_parent(user):
            kids = _parent_children(db, user, ch, spec, school)
            if kids:
                return PARENT, None, kids
        return None, None, []
    if extra is _NO_EXTRA:
        extra = db.scalar(select(ChannelExtraMember.role).where(ChannelExtraMember.channel_id == ch.id,
                                                                ChannelExtraMember.user_id == user.id))
    tid = getattr(user, "teacher_id", None)
    if spec is not None and manage and tid and tid in spec.teacher_ids:
        return TEACHER, extra, []
    if extra == TEACHER and manage:
        return TEACHER, extra, []
    sid = getattr(user, "student_id", None)
    if extra != EXCLUDED and spec is not None and sid and logic.is_channel_student(school, ch.kind, ch.ref or "", sid):
        return STUDENT, extra, []
    if extra in (TEACHER, STUDENT):
        return STUDENT, extra, []
    if _is_supervisor(user):
        return SUPERVISOR, extra, []
    return None, extra, []


def _role_for(db: Session, user: Any, ch: Channel, spec: Optional[logic.ChannelSpec], school,
              extra: Any = _NO_EXTRA) -> Optional[str]:
    """Rolle eines Kontos im Kanal: ``teacher`` > ``student`` > ``supervisor`` (Eltern ``parent``, sonst ``None``)."""
    return _access(db, user, ch, spec, school, extra)[0]


def _manages_all(user: Any, ch: Channel, spec: Optional[logic.ChannelSpec], role: Optional[str],
                 extra: Optional[str]) -> bool:
    """Darf alles im Kanal ändern? Kurs-/eigene Kursräume: alle Lehrenden; Klassenräume: Klassenleitung und
    Kursraum-Verwaltung (Zusatz-Lehrende, von der Schulleitung eingetragen)."""
    if role != TEACHER:
        return False
    if ch.kind != logic.CLASS:
        return True
    tid = getattr(user, "teacher_id", None)
    return bool(tid and spec is not None and spec.class_teacher == tid) or extra == TEACHER


def _responsible_for(user: Any, ch: Channel, role: Optional[str], manages_all: bool, created_by: Optional[int]
                     ) -> bool:
    """Darf Abgaben/Rückmeldungen einer Aufgabe sehen und bewerten? Klassenräume: nur wer sie gestellt hat (ist das
    Konto gelöscht: Klassenleitung/Kursraum-Verwaltung); sonst alle Lehrenden."""
    if role != TEACHER:
        return False
    if ch.kind != logic.CLASS:
        return True
    return created_by == getattr(user, "id", None) or (created_by is None and manages_all)


@dataclass
class Ctx:
    """Zugriffskontext einer Anfrage auf einen Kanal."""
    user: AuthUser
    ch: Channel
    spec: Optional[logic.ChannelSpec]
    role: str
    snap: Any
    extra: Optional[str] = None          # Zusatzmitglied-Rolle (teacher = Kursraum-Verwaltung)
    children: list[str] = field(default_factory=list)   # Eltern: Kinder im Kanal (mit Zugriff)
    child: Optional[str] = None          # Eltern: gewähltes Kind
    pupil_uid: Optional[int] = None      # Konto, dessen Abgaben gezeigt werden (Schüler/in bzw. Kind)

    @property
    def school(self):
        return self.snap[1]

    @property
    def teacher(self) -> bool:
        return self.role == TEACHER

    @property
    def student(self) -> bool:
        return self.role == STUDENT

    @property
    def parent(self) -> bool:
        return self.role == PARENT

    @property
    def pupil(self) -> bool:
        """Sieht nur Freigegebenes (Teilnehmende, Eltern)."""
        return self.role in (STUDENT, PARENT)

    @property
    def supervisor(self) -> bool:
        return self.role == SUPERVISOR

    @property
    def staff_view(self) -> bool:
        """Sieht alles inkl. verborgener Inhalte mit Status (Lehrende, Aufsicht)."""
        return self.role in (TEACHER, SUPERVISOR)

    @property
    def manages_all(self) -> bool:
        return _manages_all(self.user, self.ch, self.spec, self.role, self.extra)

    def may_edit(self, created_by: Optional[int]) -> bool:
        """Material/Ordner ändern, verbergen, löschen (Klassenräume: nur eigenes, außer Klassenleitung/Verwaltung)."""
        return self.teacher and (created_by == self.user.id or self.manages_all)

    def need_edit(self, created_by: Optional[int]) -> None:
        if not self.may_edit(created_by):
            raise HTTPException(403, FOREIGN_MATERIAL)

    def responsible(self, item: ChannelItem) -> bool:
        return _responsible_for(self.user, self.ch, self.role, self.manages_all, item.created_by)


def _get_channel(db: Session, channel_id: int) -> Channel:
    ch = db.get(Channel, channel_id)
    if ch is None:
        raise HTTPException(404, "Kursraum nicht gefunden")
    return ch


def _ctx(db: Session, user: AuthUser, channel_id: int, *, manage: bool = False, write: bool = False,
         child: Optional[str] = None) -> Ctx:
    """Prüft Zugriff (403 für Nicht-Mitglieder), ``manage`` = nur Lehrende, ``write`` = Lehrende/Teilnehmende;
    ``child`` = gewähltes Kind (Eltern)."""
    _need_channels(user)
    ch = _get_channel(db, channel_id)
    snap = snapshot()
    spec = _spec_for(snap[1], ch)
    role, extra, kids = _access(db, user, ch, spec, snap[1])
    if role is None:
        raise HTTPException(403, NO_TEACHER_LINK if _no_teacher_link(user) else "Kein Zugriff auf diesen Kursraum")
    if role == PARENT:
        if manage or write:
            raise HTTPException(403, "Eltern sehen Kursräume nur lesend")
        if child and child not in kids:
            raise HTTPException(403, "Kein Zugriff auf diesen Kursraum für dieses Kind")
        sel = child or kids[0]
        return Ctx(user, ch, spec, role, snap, None, kids, sel, _account_of(db, sel))
    if role == SUPERVISOR and (manage or write):
        raise HTTPException(403, "Die Schulleitung sieht Kursräume nur lesend – zum Eingreifen bitte als "
                            "Lehrende/r eintragen")
    if manage and role != TEACHER:
        raise HTTPException(403, "Nur Lehrende dieses Kursraums dürfen das")
    if (manage or write) and ch.archived:
        raise HTTPException(409, "Der Kursraum ist archiviert – Änderungen sind nicht mehr möglich")
    return Ctx(user, ch, spec, role, snap, extra, [], None, user.id if role == STUDENT else None)


def _ensure_rows(db: Session, specs: Iterable[logic.ChannelSpec]) -> dict[tuple[str, str], Channel]:
    """Kanalzeilen der automatischen Kanäle (werden bei Bedarf angelegt; Titel folgt dem Planungsdokument)."""
    wanted = {(s.kind, s.ref): s for s in specs}
    if not wanted:
        return {}
    for _attempt in range(3):
        out: dict[tuple[str, str], Channel] = {}
        for chunk in _chunks(sorted({ref for _, ref in wanted})):
            for row in db.scalars(select(Channel).where(Channel.ref.in_(chunk),
                                                        Channel.kind.in_((logic.COURSE, logic.CLASS)))):
                if (row.kind, row.ref) in wanted:
                    out[(row.kind, row.ref)] = row
        dirty = False
        for key, row in out.items():
            title = wanted[key].title
            if row.title != title:
                row.title = title
                dirty = True
        missing = [s for key, s in wanted.items() if key not in out]
        for s in missing:
            db.add(Channel(kind=s.kind, ref=s.ref, title=s.title, description="", settings=None, archived=False,
                           created_at=utcnow()))
        if not missing and not dirty:
            return out
        try:
            db.commit()
        except IntegrityError:  # gleichzeitig angelegt → neu lesen
            db.rollback()
            continue
        if not missing:
            return out
    out = {}
    for chunk in _chunks(sorted({ref for _, ref in wanted})):
        for row in db.scalars(select(Channel).where(Channel.ref.in_(chunk))):
            if (row.kind, row.ref) in wanted:
                out[(row.kind, row.ref)] = row
    return out


def _user_names(db: Session, ids: Iterable[Optional[int]]) -> dict[int, str]:
    out: dict[int, str] = {}
    for chunk in _chunks(sorted({i for i in ids if i})):
        for uid, dn, un in db.execute(select(User.id, User.display_name, User.username).where(User.id.in_(chunk))):
            out[uid] = dn or un
    return out


def _member_user_ids(db: Session, ch: Channel, spec: Optional[logic.ChannelSpec], school, *,
                     teachers_only: bool = False) -> set[int]:
    """Konten aller Mitglieder (für zielgerichtete Live-Ereignisse)."""
    ids: set[int] = set()
    tids = sorted(spec.teacher_ids) if spec else []
    sids = [] if teachers_only or spec is None else logic.channel_student_ids(school, ch.kind, ch.ref or "")
    for chunk in _chunks(tids):
        ids.update(db.scalars(select(User.id).where(User.active.is_(True), User.teacher_id.in_(chunk))))
    for chunk in _chunks(sids):
        ids.update(db.scalars(select(User.id).where(User.active.is_(True), User.role == "schueler",
                                                    User.student_id.in_(chunk))))
    stmt = select(ChannelExtraMember.user_id).where(ChannelExtraMember.channel_id == ch.id)
    if teachers_only:
        stmt = stmt.where(ChannelExtraMember.role == TEACHER)
    ids.update(db.scalars(stmt))
    return ids


def _notify(db: Session, ctx: Ctx, *, teachers_only: bool = False, extra_ids: Iterable[int] = ()) -> None:
    """Live-Ereignis ohne Inhalt an die Mitglieder (``teachers_only`` z. B. für verborgene Inhalte)."""
    try:
        ids = _member_user_ids(db, ctx.ch, ctx.spec, ctx.school, teachers_only=teachers_only)
        ids.update(extra_ids)
        ids.add(ctx.user.id)
        bus.publish("change", {"version": None, "scope": ["channels", f"channel:{ctx.ch.id}:"], "dates": []},
                    user_ids=ids)
    except Exception:  # noqa: BLE001 - Live-Ereignisse dürfen die Aktion nie stören
        log.exception("Live-Ereignis für Kursraum %s fehlgeschlagen", ctx.ch.id)


class Clock:
    """Zeitpunkt der Anfrage + Tagespläne: Freigabe „zur Stunde“ mit Verlegung am selben Tag und – bei Entfall oder
    schulfreiem Tag – Verschiebung auf die nächste stattfindende Stunde desselben Kurses (Tagesplan/Vertretung).

    Die Kanäle der geprüften Inhalte werden mit :meth:`add` bekannt gemacht (sonst gilt nur die Verlegung am Tag)."""

    def __init__(self, snap: Any, now: Optional[datetime] = None, channels: Iterable[Channel] = ()) -> None:
        self.snap = snap
        self.now = now or logic.now_utc()
        self.today = logic.local_today(self.now)
        self._plans: dict[str, Optional[dict]] = {}
        self._chan: dict[int, tuple[str, str]] = {}
        self._lessons: dict[tuple, Optional[dict[str, Any]]] = {}
        self._blocked = cgroups.Blocked()      # wegen Gruppen-Beschränkung gesperrt (nur Teilnehmende, siehe restrict)
        self.add(channels)

    @property
    def school(self):
        return self.snap[1]

    def restrict(self, db: Session, who: Any, channel_ids: Iterable[int] = (), user_id: Optional[int] = None
                 ) -> "Clock":
        """Gruppen-Beschränkungen (Material/Ordner nur für bestimmte Gruppen) für Teilnehmende berücksichtigen.

        ``who`` = :class:`Ctx` (Lehrende/Aufsicht sind nie betroffen) oder ``None`` mit ``channel_ids``/``user_id``
        (Konto der Schülerin bzw. des Kindes; ``None`` = ohne Konto → alles Beschränkte gesperrt)."""
        if isinstance(who, Ctx):
            if not who.pupil:
                return self
            channel_ids, user_id = [who.ch.id], who.pupil_uid
        blocked = cgroups.blocked_for(db, channel_ids, user_id)
        self._blocked.items |= blocked.items
        self._blocked.folders |= blocked.folders
        return self

    def add(self, channels: Iterable[Channel]) -> "Clock":
        for ch in channels:
            if ch is not None and ch.kind in (logic.COURSE, logic.CLASS) and ch.ref:
                self._chan[ch.id] = (ch.kind, ch.ref)
        return self

    def plan(self, day: date) -> Optional[dict]:
        key = day.isoformat()
        if key not in self._plans:
            try:
                self._plans[key] = day_plan(day, self.snap)[1]
            except Exception:  # noqa: BLE001 - ohne Tagesplan gilt der geplante Beginn
                log.exception("Tagesplan %s für Kursräume nicht berechenbar", key)
                self._plans[key] = None
        return self._plans[key]

    def lesson_info(self, channel_id: int, day: date, lesson_id: str, period: int) -> Optional[dict[str, Any]]:
        """Abweichung einer gebundenen Stunde (``None`` = findet wie geplant statt): ``{"status": "verlegt"|
        "verschoben", "reason", "release_at", "to"}`` – ``to`` = Ersatzstunde (``upcoming_lessons``-Eintrag)."""
        key = (channel_id, day, lesson_id, period)
        if key not in self._lessons:
            try:
                self._lessons[key] = self._lesson_info(channel_id, day, lesson_id, period)
            except Exception:  # noqa: BLE001 - im Zweifel gilt der geplante Beginn
                log.exception("Freigabe zur Stunde %s nicht berechenbar", key)
                self._lessons[key] = None
        return self._lessons[key]

    def _lesson_info(self, channel_id: int, day: date, lesson_id: str, period: int) -> Optional[dict[str, Any]]:
        school = self.school
        if day < self.today - timedelta(days=SHIFT_LOOKBACK_DAYS):
            return None
        held, reason = is_school_day(school, day, logic.channel_class(school, *(self._chan.get(channel_id) or ("", ""))))
        if held and not logic.day_has_changes(school, day):
            return None
        chan = self._chan.get(channel_id)
        if chan is None:  # Kanal unbekannt: nur Verlegung am selben Tag
            moved = logic.moved_period(self.plan(day), lesson_id, period) if held else None
            rel = logic.lesson_release_utc(school.settings, day, moved) if moved is not None else None
            return {"status": "verlegt", "reason": "verlegt", "release_at": rel, "to": None} if rel else None
        kind, ref = chan
        if held:
            entry = logic.find_lesson(school, kind, ref, day, lesson_id, period, plan=self.plan(day), now=self.now)
            if entry is None:            # Stunde gibt es (so) nicht mehr – geplanter Beginn
                return None
            if entry["status"] != "entfall":
                if entry["moved_to"] is None:
                    return None
                rel = logic.lesson_release_utc(school.settings, day, entry["moved_to"])
                return {"status": "verlegt", "reason": "verlegt", "release_at": rel, "to": None} if rel else None
            reason = "Entfall"
        les = logic.index_for(school).lessons.get(lesson_id)
        nxt = logic.next_held_lesson(school, kind, ref, day, period, course_id=les.course_id if les else None,
                                     plan_for=self.plan, now=self.now)
        return {"status": "verschoben", "reason": reason or "schulfrei", "release_at": nxt["release_at"] if nxt else None,
                "to": nxt}

    def release(self, obj: Any) -> Optional[datetime]:
        """Freigabezeitpunkt (UTC) von Material/Ordner: geplant (``visible_from``) bzw. Beginn der (Ersatz-)Stunde."""
        vis = obj.effective_visibility if isinstance(obj, ChannelFolder) else obj.visibility
        if vis == "scheduled":
            return obj.visible_from
        if vis != "lesson":
            return None
        base = obj.visible_from
        if not obj.lesson_date or not obj.lesson_id or obj.lesson_period is None:
            return base
        try:
            day = date.fromisoformat(obj.lesson_date)
        except ValueError:
            return base
        info = self.lesson_info(obj.channel_id, day, obj.lesson_id, obj.lesson_period)
        return base if info is None else info["release_at"]

    def folder_states(self, folders: Iterable[ChannelFolder]) -> dict[int, logic.Visibility]:
        folders = list(folders)
        states = logic.folder_states(folders, now=self.now, release_of=self.release)
        if self._blocked.folders:           # Gruppen-Beschränkung: Ordner samt Unterordnern nicht sichtbar
            children: dict[int, list[int]] = defaultdict(list)
            for f in folders:
                if f.parent_id is not None:
                    children[f.parent_id].append(f.id)
            stack = [fid for fid in self._blocked.folders if fid in states]
            while stack:
                fid = stack.pop()
                if states[fid].code != "group_hidden":
                    states[fid] = logic.Visibility(False, "group_hidden")
                    stack.extend(children.get(fid, ()))
        return states

    def visibility(self, item: ChannelItem, states: dict[int, logic.Visibility]) -> logic.Visibility:
        if item.id in self._blocked.items:
            return logic.Visibility(False, "group_hidden")
        folder = states.get(item.folder_id) if item.folder_id is not None else None
        vis = logic.item_visibility(item.visibility, self.release(item), now=self.now, folder=folder)
        if vis.visible and folder is not None and folder.release_at is not None:
            vis = logic.Visibility(True, "visible", max(folder.release_at, vis.release_at or folder.release_at))
        return vis


def _folders(db: Session, channel_id: int) -> list[ChannelFolder]:
    return list(db.scalars(select(ChannelFolder).where(ChannelFolder.channel_id == channel_id)
                           .order_by(ChannelFolder.position, ChannelFolder.id)))


def _load_items(db: Session, channel_ids: Iterable[int]) -> list[tuple[ChannelItem, bool]]:
    """Material ohne Textinhalt (``body_enc`` wird nur bei Bedarf nachgeladen) + Merker „hat Text“."""
    out: list[tuple[ChannelItem, bool]] = []
    has_body = (func.length(ChannelItem.body_enc) > 0).label("has_body")
    for chunk in _chunks(sorted(set(channel_ids))):
        stmt = (select(ChannelItem, has_body).options(defer(ChannelItem.body_enc))
                .where(ChannelItem.channel_id.in_(chunk))
                .order_by(ChannelItem.position, ChannelItem.created_at, ChannelItem.id))
        out.extend((item, bool(flag)) for item, flag in db.execute(stmt))
    return out


def _get_item(db: Session, ctx: Ctx, item_id: int) -> ChannelItem:
    item = db.get(ChannelItem, item_id)
    if item is None or item.channel_id != ctx.ch.id:
        raise HTTPException(404, "Material nicht gefunden")
    return item


def _get_folder(db: Session, ctx: Ctx, folder_id: Optional[int]) -> Optional[ChannelFolder]:
    if folder_id is None:
        return None
    folder = db.get(ChannelFolder, folder_id)
    if folder is None or folder.channel_id != ctx.ch.id:
        raise HTTPException(404, "Ordner nicht gefunden")
    return folder


def _visible_item_or_404(db: Session, ctx: Ctx, item_id: int, clock: Clock) -> tuple[ChannelItem, logic.Visibility]:
    item = _get_item(db, ctx, item_id)
    states = clock.folder_states(_folders(db, ctx.ch.id)) if item.folder_id else {}
    vis = clock.visibility(item, states)
    if ctx.pupil:
        gate = progress.Progress(db, [ctx.ch.id], [ctx.pupil_uid]).gate(ctx.pupil_uid, progress.ELEMENT_ITEM, item.id,
                                                                       vis, ctx.ch.id)
        if not gate.show:
            raise HTTPException(404, "Material nicht gefunden")
        if gate.locked:
            raise HTTPException(403, f"Noch gesperrt – verfügbar, sobald {gate.text}")
    return item, vis


def _student_count(ctx: Ctx, db: Session) -> int:
    """Teilnehmende (Planungsdokument + Zusatzmitglieder) – Erwartungswert für Abgaben."""
    n = len(logic.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "")) if ctx.spec else 0
    n += int(db.scalar(select(func.count()).select_from(ChannelExtraMember).where(
        ChannelExtraMember.channel_id == ctx.ch.id, ChannelExtraMember.role == STUDENT)) or 0)
    return n


def _lesson_out(school, item: Any, clock: Optional[Clock] = None) -> Optional[dict[str, Any]]:
    """Gebundene Stunde (Material oder Ordner); mit ``clock`` auch ``shift`` = Entfall/Verlegung → Ersatzstunde."""
    vis = item.effective_visibility if isinstance(item, ChannelFolder) else item.visibility
    if vis != "lesson" or not item.lesson_date or item.lesson_period is None:
        return None
    try:
        day = date.fromisoformat(item.lesson_date)
    except ValueError:
        return None
    les = logic.index_for(school).lessons.get(item.lesson_id or "")
    length = les.length if les is not None and les.start == item.lesson_period else 1
    out: dict[str, Any] = {"date": item.lesson_date, "lesson_id": item.lesson_id, "period": item.lesson_period,
                           "label": logic.lesson_label(school.settings, day, item.lesson_period, length),
                           "key": logic.lesson_key(day, item.lesson_id or "", item.lesson_period), "shift": None}
    info = clock.lesson_info(item.channel_id, day, item.lesson_id or "", item.lesson_period) if clock else None
    if info is not None:
        to = info.get("to")
        out["shift"] = {"status": info["status"], "reason": info["reason"], "release_at": iso(info["release_at"]),
                        "to_label": to["label"] if to else None, "to_date": to["date"] if to else None}
    return out


def _available_at(item: ChannelItem, vis: logic.Visibility) -> datetime:
    """Seit wann ist das Material für Teilnehmende da (für „neu“)?"""
    if vis.release_at:
        return max(vis.release_at, item.created_at)
    if item.visibility == "visible" and item.visible_from:
        return item.visible_from
    return item.created_at


def takes_submissions(item: ChannelItem) -> bool:
    """Aufgaben immer; anderes Material, wenn „Abgabe möglich“ gesetzt ist."""
    return item.type == "assignment" or bool(item.submittable)


def _apply_material_flags(item: ChannelItem, lesson_material: bool, material_date: Optional[date], submittable: bool,
                          clock: Clock) -> None:
    """Unterrichtsmaterial (Datum: angegeben, sonst Datum der gebundenen Stunde, sonst heute) und „Abgabe möglich“."""
    item.lesson_material = bool(lesson_material)
    if item.lesson_material:
        day = material_date.isoformat() if material_date else (item.lesson_date or clock.today.isoformat())
        item.material_date = day
    else:
        item.material_date = None
    item.submittable = bool(submittable) and item.type != "assignment"


def _items_out(db: Session, ctx: Ctx, rows: list[tuple[ChannelItem, bool]], hidden: dict[int, logic.Visibility],
               clock: Clock, last_seen: Optional[datetime]) -> list[dict[str, Any]]:
    """Material-Liste für die Rolle (Teilnehmende nur Sichtbares, Lehrende/Aufsicht alles mit Status)."""
    shown: list[tuple[ChannelItem, bool, logic.Visibility]] = []
    prog = progress.Progress(db, {item.channel_id for item, _ in rows} or [ctx.ch.id], [ctx.pupil_uid])
    gates: dict[int, progress.Gate] = {}
    for item, has_body in rows:
        vis = clock.visibility(item, hidden)
        if ctx.pupil:
            gate = gates[item.id] = prog.gate(ctx.pupil_uid, progress.ELEMENT_ITEM, item.id, vis, item.channel_id)
            if not gate.show:
                continue
        shown.append((item, has_body, vis))
    track = ctx.student or (ctx.parent and bool(ctx.ch.setting("progress_parents")))
    if track and prog.rules:
        prog.prefetch([ctx.pupil_uid])
    file_ids: list[str] = []
    for item, _, _ in shown:
        if item.file_id:
            file_ids.append(item.file_id)
        file_ids.extend(item.attachment_ids or [])
    infos = {f["id"]: f for f in files.files_info(db, file_ids, ctx.user, check_access=False)}
    assignment_ids = [item.id for item, _, _ in shown if takes_submissions(item)]
    own: dict[int, AssignmentSubmission] = {}
    counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    if assignment_ids and ctx.pupil:
        for chunk in _chunks(assignment_ids if ctx.pupil_uid else []):
            for sub in db.scalars(select(AssignmentSubmission)
                                  .options(defer(AssignmentSubmission.text_enc),
                                           defer(AssignmentSubmission.feedback_enc))
                                  .where(AssignmentSubmission.item_id.in_(chunk),
                                         AssignmentSubmission.student_user_id == ctx.pupil_uid)):
                own[sub.item_id] = sub
    elif assignment_ids:
        for chunk in _chunks(assignment_ids):
            for item_id, status, n in db.execute(
                    select(AssignmentSubmission.item_id, AssignmentSubmission.status, func.count())
                    .where(AssignmentSubmission.item_id.in_(chunk), AssignmentSubmission.submitted_at.is_not(None))
                    .group_by(AssignmentSubmission.item_id, AssignmentSubmission.status)):
                counts[item_id][status] += int(n)
    expected = _student_count(ctx, db) if assignment_ids and ctx.staff_view else 0
    names = _user_names(db, (item.created_by for item, _, _ in shown)) if ctx.staff_view else {}
    threshold = last_seen or (clock.now - timedelta(days=NEW_DAYS))
    ovr = at.due_overrides(db, assignment_ids, ctx.pupil_uid) if ctx.pupil and ctx.pupil_uid else {}
    out = []
    for item, has_body, vis in shown:
        available = _available_at(item, vis)
        entry: dict[str, Any] = {
            "id": item.id, "channel_id": item.channel_id, "folder_id": item.folder_id, "type": item.type,
            "type_label": TYPE_LABELS.get(item.type, item.type), "title": item.title,
            "url": item.url if item.type == "link" else None,
            "file": infos.get(item.file_id) if item.file_id else None,
            "attachments": [infos[i] for i in item.attachment_ids or [] if i in infos],
            "has_body": has_body, "position": item.position, "due_at": iso(item.due_at),
            "allow_late": bool(item.allow_late), "created_at": iso(item.created_at),
            "updated_at": iso(item.updated_at), "available_at": iso(available), "visible": vis.visible,
            "is_new": bool(vis.visible and available > threshold and item.created_by != ctx.user.id),
            "lesson": _lesson_out(ctx.school, item, clock if ctx.staff_view else None),
            "lesson_material": bool(item.lesson_material), "material_date": item.material_date,
            "submittable": takes_submissions(item), "info_card": bool(item.info_card),
        }
        if ctx.staff_view:
            entry.update({"visibility": item.visibility, "state": vis.code,
                          "state_label": STATE_LABELS.get(vis.code, vis.code),
                          "visible_from": iso(item.visible_from), "release_at": iso(vis.release_at),
                          "created_by_name": names.get(item.created_by or 0, ""),
                          "own": item.created_by == ctx.user.id, "can_edit": ctx.may_edit(item.created_by)})
        rule = prog.rule(progress.ELEMENT_ITEM, item.id)
        if ctx.staff_view:
            tree = prog.avail.get((progress.ELEMENT_ITEM, item.id))
            entry["completion_rule"] = ({"mode": rule.mode, "mode_label": progress.MODE_LABELS.get(rule.mode, rule.mode),
                                         "pass_percent": rule.pass_percent} if rule else None)
            entry["availability"] = ({"tree": tree, "text": prog.describe(progress.ELEMENT_ITEM, item.id, item.channel_id)}
                                     if tree else None)
        gate = gates.get(item.id)
        if rule is not None and track and not (gate and gate.locked):
            entry["completion"] = {"mode": rule.mode, "mode_label": progress.MODE_LABELS.get(rule.mode, rule.mode),
                                   "done": bool(prog.done(ctx.pupil_uid, progress.ELEMENT_ITEM, item.id)),
                                   "can_toggle": bool(ctx.student and rule.mode == "manual" and not ctx.ch.archived)}
        if takes_submissions(item):
            if ctx.staff_view:
                entry["can_grade"] = ctx.responsible(item)
            if ctx.pupil:
                sub = own.get(item.id)
                my_due = at.effective_due(item.due_at, ovr.get(item.id))
                status = logic.submission_status(my_due, sub.submitted_at if sub else None,
                                                 sub.status if sub else None, clock.now)
                entry["submission"] = {"status": status, "status_label": logic.SUBMISSION_LABELS.get(status, status),
                                       "submitted_at": iso(sub.submitted_at) if sub else None,
                                       "has_feedback": bool(sub and sub.feedback_at), "due_at": iso(my_due)}
            elif ctx.supervisor or ctx.responsible(item):
                c = counts.get(item.id, {})
                submitted = sum(c.values())
                entry["submissions"] = {"expected": expected, "submitted": submitted,
                                        "to_grade": sum(c.get(s, 0) for s in OPEN_SUBMISSIONS),
                                        "graded": c.get("bewertet", 0), "returned": c.get("zurueckgegeben", 0),
                                        "late": c.get("verspaetet", 0)}
        if gate is not None and gate.locked:
            progress.mask_locked(entry, gate)
        out.append(entry)
    return out


def _folders_out(ctx: Ctx, folders: list[ChannelFolder], states: dict[int, logic.Visibility],
                 clock: Optional[Clock] = None) -> list[dict[str, Any]]:
    out = []
    for f in folders:
        st = states.get(f.id)
        if ctx.pupil and st is not None and not st.visible:
            continue
        entry: dict[str, Any] = {"id": f.id, "parent_id": f.parent_id, "name": f.name, "position": f.position}
        if ctx.staff_view:
            code = st.code if st is not None else "visible"
            entry.update({"hidden": bool(f.hidden), "hidden_effective": bool(st is not None and not st.visible),
                          "visibility": f.effective_visibility, "state": code,
                          "state_label": STATE_LABELS.get(code, code), "visible_from": iso(f.visible_from),
                          "release_at": iso(st.release_at) if st is not None else None,
                          "lesson": _lesson_out(ctx.school, f, clock), "own": f.created_by == ctx.user.id,
                          "can_edit": ctx.may_edit(f.created_by)})
        out.append(entry)
    return out


def _next_release(rows: list[tuple[ChannelItem, bool]], states: dict[int, logic.Visibility], clock: Clock
                  ) -> Optional[datetime]:
    """Nächster Freigabezeitpunkt (Material oder Ordner) innerhalb von 24 h (damit offene Seiten pünktlich neu
    laden)."""
    soon = clock.now + timedelta(hours=24)
    candidates = [st.release_at for st in states.values() if not st.visible]
    for item, _ in rows:
        if item.visibility in ("scheduled", "lesson") or item.folder_id is not None:
            vis = clock.visibility(item, states)
            if not vis.visible:
                candidates.append(vis.release_at)
    future = [rel for rel in candidates if rel and clock.now < rel <= soon]
    return min(future) if future else None


def _channel_out(ch: Channel, spec: Optional[logic.ChannelSpec], role: Optional[str], school,
                 stats: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    idx = logic.index_for(school)
    teachers = [idx.teacher_name(t) for t in (spec.teacher_ids if spec else ())]
    return {
        "id": ch.id, "kind": ch.kind, "kind_label": KIND_LABELS.get(ch.kind, ch.kind), "ref": ch.ref,
        "title": spec.title if spec else ch.title, "subtitle": spec.subtitle if spec else "",
        "description": ch.description or "", "role": role, "role_label": ROLE_LABELS.get(role or "", ""),
        "classes": list(spec.class_ids) if spec else [], "subject": spec.subject if spec else None,
        "subject_name": spec.subject_name if spec else None, "course_id": spec.course_id if spec else None,
        "part": spec.part if spec else None, "grade": spec.grade if spec else None,
        "teachers": teachers[:12], "teacher_count": len(teachers),
        "class_teacher": idx.teacher_name(spec.class_teacher) if spec and spec.class_teacher else None,
        "archived": bool(ch.archived), "orphaned": ch.kind != logic.CUSTOM and spec is None,
        "settings": {"students_can_post": bool(ch.setting("students_can_post")),
                     "students_can_reply": bool(ch.setting("students_can_reply")),
                     "progress_parents": bool(ch.setting("progress_parents"))},
        **(stats or {}),
    }


def _channel_stats(db: Session, user: AuthUser, entries: list[tuple[Channel, Optional[logic.ChannelSpec], str]],
                   clock: Clock, pupil_uid: Optional[int] = None) -> dict[int, dict[str, Any]]:
    """Zähler je Kanal: neues Material/neue Beiträge seit dem letzten Besuch, offene Aufgaben, zu bewerten
    (Klassenräume: nur eigene Aufgaben). ``pupil_uid`` = Konto des Kindes (Elternansicht)."""
    member = {ch.id: role for ch, _, role in entries if role in (TEACHER, STUDENT, PARENT)}
    pupil_uid = pupil_uid if pupil_uid is not None else user.id
    clock.add(ch for ch, _, _ in entries)
    clock.restrict(db, None, [ch.id for ch, _, role in entries if role in (STUDENT, PARENT)], pupil_uid)
    by_id = {ch.id: (ch, spec) for ch, spec, _ in entries}
    teacher_extra = set(db.scalars(select(ChannelExtraMember.channel_id).where(
        ChannelExtraMember.user_id == user.id, ChannelExtraMember.role == TEACHER))) if TEACHER in member.values() \
        else set()
    stats: dict[int, dict[str, Any]] = {cid: {"new_items": 0, "new_posts": 0, "open_assignments": 0, "to_grade": 0,
                                              "last_activity": None} for cid in member}
    if not member:
        return stats
    ids = sorted(member)
    reads: dict[int, datetime] = {}
    hidden_by_channel: dict[int, dict[int, logic.Visibility]] = {}
    folders_by_channel: dict[int, list[Any]] = defaultdict(list)
    for chunk in _chunks(ids):
        for cid, seen in db.execute(select(ChannelRead.channel_id, ChannelRead.last_seen_at)
                                    .where(ChannelRead.user_id == user.id, ChannelRead.channel_id.in_(chunk))):
            reads[cid] = seen
        for f in db.scalars(select(ChannelFolder).where(ChannelFolder.channel_id.in_(chunk))):
            folders_by_channel[f.channel_id].append(f)
    for cid in ids:
        hidden_by_channel[cid] = clock.folder_states(folders_by_channel.get(cid, ()))
    default_seen = clock.now - timedelta(days=NEW_DAYS)
    rows = _load_items(db, ids)
    student_assignments: list[ChannelItem] = []
    teacher_assignments: dict[int, int] = {}
    for item, _ in rows:
        role = member[item.channel_id]
        vis = clock.visibility(item, hidden_by_channel[item.channel_id])
        st = stats[item.channel_id]
        if vis.visible:
            available = _available_at(item, vis)
            if available > reads.get(item.channel_id, default_seen) and item.created_by != user.id:
                st["new_items"] += 1
            if st["last_activity"] is None or available > st["last_activity"]:
                st["last_activity"] = available
        if item.type == "assignment":
            if role in (STUDENT, PARENT) and vis.visible:
                student_assignments.append(item)
            elif role == TEACHER:
                ch, spec = by_id[item.channel_id]
                all_ = _manages_all(user, ch, spec, TEACHER, TEACHER if ch.id in teacher_extra else None)
                if _responsible_for(user, ch, TEACHER, all_, item.created_by):
                    teacher_assignments[item.id] = item.channel_id
    if student_assignments:
        subs: dict[int, AssignmentSubmission] = {}
        for chunk in _chunks([i.id for i in student_assignments]):
            for sub in db.scalars(select(AssignmentSubmission)
                                  .options(defer(AssignmentSubmission.text_enc),
                                           defer(AssignmentSubmission.feedback_enc))
                                  .where(AssignmentSubmission.item_id.in_(chunk),
                                         AssignmentSubmission.student_user_id == pupil_uid)):
                subs[sub.item_id] = sub
        ovr = at.due_overrides(db, [i.id for i in student_assignments], pupil_uid)
        for item in student_assignments:
            sub = subs.get(item.id)
            status = logic.submission_status(at.effective_due(item.due_at, ovr.get(item.id)),
                                             sub.submitted_at if sub else None, sub.status if sub else None, clock.now)
            if status in ("offen", "ueberfaellig", "zurueckgegeben"):
                stats[item.channel_id]["open_assignments"] += 1
    if teacher_assignments:
        for chunk in _chunks(sorted(teacher_assignments)):
            for item_id, n in db.execute(select(AssignmentSubmission.item_id, func.count())
                                         .where(AssignmentSubmission.item_id.in_(chunk),
                                                AssignmentSubmission.status.in_(OPEN_SUBMISSIONS))
                                         .group_by(AssignmentSubmission.item_id)):
                stats[teacher_assignments[item_id]]["to_grade"] += int(n)
    since = min([*reads.values(), default_seen]) if reads else default_seen
    for chunk in _chunks(ids):
        for cid, created, author in db.execute(
                select(ChannelPost.channel_id, ChannelPost.created_at, ChannelPost.author_id)
                .where(ChannelPost.channel_id.in_(chunk), ChannelPost.deleted_at.is_(None),
                       ChannelPost.created_at > since)):
            st = stats[cid]
            if created > reads.get(cid, default_seen) and author != user.id:
                st["new_posts"] += 1
            if st["last_activity"] is None or created > st["last_activity"]:
                st["last_activity"] = created
    for st in stats.values():
        st["last_activity"] = iso(st["last_activity"])
    return stats


def _permissions_out(ctx: Ctx) -> dict[str, bool]:
    active = not ctx.ch.archived
    return {
        "manage": ctx.teacher and active,
        "post": active and (ctx.teacher or (ctx.student and bool(ctx.ch.setting("students_can_post")))),
        "reply": active and (ctx.teacher or (ctx.student and bool(ctx.ch.setting("students_can_reply")))),
        "moderate": ctx.teacher and active,
        "submit": ctx.student and active,
        "view_submissions": ctx.teacher,
        "supervise": ctx.supervisor,
        "add_members": (_is_supervisor(ctx.user) or ctx.teacher) and not ctx.parent,
        "add_teachers": _is_supervisor(ctx.user),
        "archive": False,
        "lessons": ctx.staff_view and ctx.ch.kind != logic.CUSTOM,
        "manage_all": ctx.manages_all and active,
        "progress": ctx.teacher,                              # Fortschrittsübersicht, Abschluss- und Freigaberegeln
        "progress_parents": ctx.parent and bool(ctx.ch.setting("progress_parents")),
        "trash": ctx.teacher,                                 # Papierkorb ansehen (Wiederherstellen/Löschen: Recht)
        "trash_restore": ctx.teacher and active and has(ctx.user, "channels.trash"),
        "parent": ctx.parent,
        "members": not ctx.parent,
    }


def _check_item_capacity(db: Session, channel_id: int, extra: int) -> None:
    n = int(db.scalar(select(func.count()).select_from(ChannelItem).where(ChannelItem.channel_id == channel_id))
            or 0)
    if n + extra > MAX_ITEMS:
        raise HTTPException(409, f"Höchstens {MAX_ITEMS} Materialien je Kursraum")


def _next_position(db: Session, channel_id: int, folder_id: Optional[int], model=ChannelItem) -> int:
    col = model.folder_id if model is ChannelItem else model.parent_id
    cond = col.is_(None) if folder_id is None else col == folder_id
    current = db.scalar(select(func.max(model.position)).where(model.channel_id == channel_id, cond))
    return int(current or 0) + 1 if current is not None else 0


def _visibility_fields(ctx: Ctx, visibility: str, visible_from: Optional[datetime],
                       lesson: Optional[LessonRef], clock: Clock) -> dict[str, Any]:
    """Prüft die Sichtbarkeit und liefert die zu speichernden Felder (``next_lesson`` → nächste stattfindende,
    noch nicht begonnene Stunde des Kursraums; in Klassenräumen die eigene, sonst irgendeine der Klasse)."""
    empty = {"lesson_date": None, "lesson_id": None, "lesson_period": None}
    if visibility == "next_lesson":
        if ctx.ch.kind == logic.CUSTOM or ctx.spec is None:
            raise HTTPException(422, "Dieser Kursraum hat keine Unterrichtsstunden im Stundenplan")
        tid = getattr(ctx.user, "teacher_id", None) if ctx.ch.kind == logic.CLASS else None
        nxt = None
        for teacher in dict.fromkeys([tid, None]):
            nxt = logic.next_held_lesson(ctx.school, ctx.ch.kind, ctx.ch.ref or "", clock.today, -1,
                                         teacher_id=teacher, plan_for=clock.plan, now=clock.now, not_started=True)
            if nxt is not None:
                break
        if nxt is None:
            raise HTTPException(422, "In den nächsten acht Wochen findet keine Stunde dieses Kursraums statt")
        visibility = "lesson"
        lesson = LessonRef(date=date.fromisoformat(nxt["date"]), lesson_id=nxt["lesson_id"], period=nxt["period"])
    if visibility == "scheduled":
        when = _to_utc(visible_from, "die Freigabe")
        if when is None:
            raise HTTPException(422, "Bitte den Zeitpunkt der Freigabe angeben")
        return {"visibility": "scheduled", "visible_from": when, **empty}
    if visibility == "lesson":
        if lesson is None:
            raise HTTPException(422, "Bitte die Unterrichtsstunde für die Freigabe wählen")
        if ctx.ch.kind == logic.CUSTOM or ctx.spec is None:
            raise HTTPException(422, "Dieser Kursraum hat keine Unterrichtsstunden im Stundenplan")
        school = ctx.school
        ok, reason = is_school_day(school, lesson.date, logic.channel_class(school, ctx.ch.kind, ctx.ch.ref or ""))
        if not ok:
            raise HTTPException(422, f"Am {lesson.date.strftime('%d.%m.%Y')} ist kein Unterricht ({reason})")
        entry = logic.find_lesson(school, ctx.ch.kind, ctx.ch.ref or "", lesson.date, lesson.lesson_id,
                                  lesson.period, now=clock.now)
        if entry is None:
            raise HTTPException(422, "Diese Unterrichtsstunde gehört nicht zu diesem Kursraum oder findet an diesem "
                                "Tag nicht statt")
        planned = logic.lesson_release_utc(school.settings, lesson.date, lesson.period)
        if planned is None:
            raise HTTPException(422, "Für diese Stunde ist im Zeitraster keine Uhrzeit hinterlegt")
        return {"visibility": "lesson", "visible_from": planned, "lesson_date": lesson.date.isoformat(),
                "lesson_id": lesson.lesson_id, "lesson_period": lesson.period}
    return {"visibility": visibility, "visible_from": None, **empty}


def _apply_visibility(item: ChannelItem, fields: dict[str, Any], now: datetime) -> bool:
    """Setzt die Sichtbarkeitsfelder; ``visible`` merkt sich den Zeitpunkt der Freigabe (für „neu“)."""
    before = (item.visibility, item.visible_from, item.lesson_date, item.lesson_id, item.lesson_period)
    if fields["visibility"] == "visible":
        fields = {**fields, "visible_from": item.visible_from if item.visibility == "visible" else now}
    for key, value in fields.items():
        setattr(item, key, value)
    return before != (item.visibility, item.visible_from, item.lesson_date, item.lesson_id, item.lesson_period)


def _apply_folder_visibility(folder: ChannelFolder, fields: dict[str, Any], now: datetime) -> bool:
    """Wie :func:`_apply_visibility` für Ordner; ``hidden`` bleibt mit ``visibility == "hidden"`` abgeglichen."""
    before = (folder.effective_visibility, folder.visible_from, folder.lesson_date, folder.lesson_id,
              folder.lesson_period)
    vis = fields["visibility"]
    fields = dict(fields)
    if vis == "visible":
        fields["visible_from"] = folder.visible_from if folder.effective_visibility == "visible" else now
    for key, value in fields.items():
        setattr(folder, key, value)
    folder.hidden = vis == "hidden"
    return before != (folder.effective_visibility, folder.visible_from, folder.lesson_date, folder.lesson_id,
                      folder.lesson_period)


def _stem(filename: str) -> str:
    stem, _ = files.split_ext(filename or "")
    return logic.clean_name(stem or filename, 200) or "Datei"


def _delete_item_rows(db: Session, items: Iterable[ChannelItem]) -> int:
    """Löscht Materialien inkl. ihrer Dateien, Abgaben und Abgabe-Dateien (ohne Commit)."""
    n = 0
    for item in items:
        for sub_id in list(db.scalars(select(AssignmentSubmission.id).where(AssignmentSubmission.item_id == item.id))):
            files.delete_for_ref(db, REF_SUBMISSION, sub_id, hard=True)
            sub = db.get(AssignmentSubmission, sub_id)
            if sub is not None:
                db.delete(sub)
        files.delete_for_ref(db, REF_ITEM, item.id, hard=True)
        db.delete(item)
        n += 1
    db.flush()
    return n


def _trash_rows(*, items: Iterable[ChannelItem], folders: Iterable[ChannelFolder], user: Any) -> str:
    """Legt Material und Ordner (eine Löschaktion) in den Papierkorb; Abgaben, Dateien und Regeln bleiben erhalten.
    Rückgabe: Papierkorb-Gruppe (verbindet alles, was zusammen gelöscht wurde)."""
    group = uuid.uuid4().hex
    now = utcnow()
    for row in (*items, *folders):
        row.deleted_at, row.deleted_by, row.trash_group = now, getattr(user, "id", None), group
    return group


def _folder_depth(folders_by_id: dict[int, ChannelFolder], folder_id: Optional[int]) -> int:
    depth, cur, seen = 0, folder_id, set()
    while cur is not None and cur in folders_by_id and cur not in seen:
        seen.add(cur)
        depth += 1
        cur = folders_by_id[cur].parent_id
    return depth


def _subtree_height(folders: list[ChannelFolder], folder_id: int) -> int:
    children: dict[Optional[int], list[int]] = defaultdict(list)
    for f in folders:
        children[f.parent_id].append(f.id)

    def height(fid: int, depth: int = 0) -> int:
        if depth > 64:
            return depth
        return 1 + max((height(c, depth + 1) for c in children.get(fid, ())), default=0)

    return height(folder_id)


# =========================================================================== Datei-Zugriff (Basisdienst)
def _ref_int(meta: Any) -> Optional[int]:
    try:
        return int(meta.ref_id or "")
    except (TypeError, ValueError):
        return None


def _file_access_item(db: Session, user: Any, meta: Any) -> bool:
    """Material-Dateien: Lehrende/Aufsicht immer, Teilnehmende und Eltern nur bei freigegebenem Material."""
    item = db.get(ChannelItem, _ref_int(meta) or 0)
    if item is None or (meta.id != item.file_id and meta.id not in (item.attachment_ids or [])):
        return False
    ch = db.get(Channel, item.channel_id)
    if ch is None:
        return False
    snap = snapshot()
    role = _role_for(db, user, ch, _spec_for(snap[1], ch), snap[1])
    if role in (TEACHER, SUPERVISOR):
        return True
    if role not in (STUDENT, PARENT):
        return False
    uids: list[Optional[int]] = [user.id] if role == STUDENT else         [acc.id for acc in _child_accounts(db, getattr(user, "student_ids", None) or []).values()] or [None]
    prog = progress.Progress(db, [ch.id], uids)

    def visible_for(uid: Optional[int]) -> logic.Visibility:
        clock = Clock(snap, channels=[ch]).restrict(db, None, [ch.id], uid)      # Gruppen-Beschränkung je Konto
        states = clock.folder_states(_folders(db, ch.id)) if item.folder_id else {}
        return clock.visibility(item, states)

    return any(prog.gate(u, progress.ELEMENT_ITEM, item.id, visible_for(u), ch.id) == progress.Gate(True)
               for u in uids)


def _file_access_submission(db: Session, user: Any, meta: Any) -> bool:
    """Abgabe-/Rückmeldungsdateien: die Schülerin/der Schüler der Abgabe und die Lehrenden (nicht die Aufsicht)."""
    sub = db.get(AssignmentSubmission, _ref_int(meta) or 0)
    if sub is None:
        return False
    in_versions = meta.id in at.versioned_file_ids(db, sub.item_id)          # frühere Versionen (Überarbeitung)
    if meta.id not in [*(sub.file_ids or []), *(sub.feedback_file_ids or [])] and not in_versions:
        return False
    if sub.student_user_id == getattr(user, "id", None):
        return True
    if sub.group_id and at.file_in_user_rows(db, sub.item_id, getattr(user, "id", None), meta.id):
        return True                                                         # Gruppenabgabe: Datei steht in der eigenen Zeile
    item = db.get(ChannelItem, sub.item_id)
    ch = db.get(Channel, item.channel_id) if item else None
    if ch is None or item is None:
        return False
    snap = snapshot()
    if _is_parent(user):    # Eltern: nur die Abgabe/Rückmeldung des eigenen Kindes (mit Zugriff auf Kursräume)
        sid = sub.student_id
        return bool(sid and sid in (getattr(user, "student_ids", None) or [])
                    and pa.parent_may_see(db, sid, pa.AREA_CHANNELS, school=snap[1]))
    spec = _spec_for(snap[1], ch)
    role, extra, _ = _access(db, user, ch, spec, snap[1])
    return _responsible_for(user, ch, role, _manages_all(user, ch, spec, role, extra), item.created_by)


def _file_access_post(db: Session, user: Any, meta: Any) -> bool:
    """Anhänge der Pinnwand: alle, die den Kanal lesen dürfen (gelöschte Beiträge: niemand)."""
    post = db.get(ChannelPost, _ref_int(meta) or 0)
    if post is None or post.deleted_at is not None or meta.id not in (post.attachment_ids or []):
        return False
    ch = db.get(Channel, post.channel_id)
    if ch is None:
        return False
    snap = snapshot()
    return _role_for(db, user, ch, _spec_for(snap[1], ch), snap[1]) is not None


files.register_access_check(REF_ITEM, _file_access_item)
files.register_access_check(REF_SUBMISSION, _file_access_submission)
files.register_access_check(REF_POST, _file_access_post)
files.register_purpose(PURPOSE_MATERIAL, extra_kinds=["code"])      # Quelltext (Informatik) nur als Download
files.register_purpose(PURPOSE_SUBMISSION, extra_kinds=["code"])
files.register_purpose(PURPOSE_POST, max_mb=10)


# =========================================================================== Übersicht (Startseite)
def _overview_entry(ch: Channel, spec: Optional[logic.ChannelSpec], item: ChannelItem, **extra: Any) -> dict:
    return {"channel_id": ch.id, "channel_title": spec.title if spec else ch.title, "item_id": item.id,
            "title": item.title, "type": item.type, "type_label": TYPE_LABELS.get(item.type, item.type),
            "due_at": iso(item.due_at), **extra}


def _pupil_lists(db: Session, user_id: Optional[int], channels: dict[int, tuple[Channel, Optional[logic.ChannelSpec]]],
                 clock: Clock, *, with_new: bool) -> tuple[list[dict], list[dict], int]:
    """Neues Material und fällige Aufgaben für eine/n Schüler/in (``user_id`` = Konto, ``None`` = ohne Konto)."""
    ids = sorted(channels)
    if not ids:
        return [], [], 0
    folders_by_channel: dict[int, list[Any]] = defaultdict(list)
    reads: dict[int, datetime] = {}
    for chunk in _chunks(ids):
        for f in db.scalars(select(ChannelFolder).where(ChannelFolder.channel_id.in_(chunk))):
            folders_by_channel[f.channel_id].append(f)
        if user_id:
            for cid, seen in db.execute(select(ChannelRead.channel_id, ChannelRead.last_seen_at)
                                        .where(ChannelRead.user_id == user_id, ChannelRead.channel_id.in_(chunk))):
                reads[cid] = seen
    clock.add(ch for ch, _ in channels.values())
    clock.restrict(db, None, ids, user_id)
    hidden = {cid: clock.folder_states(folders_by_channel.get(cid, ())) for cid in ids}
    default_seen = clock.now - timedelta(days=NEW_DAYS)
    new_items: list[tuple[datetime, dict]] = []
    assignments: list[ChannelItem] = []
    prog = progress.Progress(db, ids, [user_id])
    for item, _ in _load_items(db, ids):
        vis = clock.visibility(item, hidden[item.channel_id])
        gate = prog.gate(user_id, progress.ELEMENT_ITEM, item.id, vis, item.channel_id)
        if not gate.show or gate.locked:
            continue
        ch, spec = channels[item.channel_id]
        if item.type == "assignment":
            assignments.append(item)
        if with_new:
            available = _available_at(item, vis)
            if available > reads.get(item.channel_id, default_seen) and item.created_by != user_id:
                new_items.append((available, _overview_entry(ch, spec, item, available_at=iso(available))))
    subs: dict[int, AssignmentSubmission] = {}
    if user_id and assignments:
        for chunk in _chunks([a.id for a in assignments]):
            for sub in db.scalars(select(AssignmentSubmission)
                                  .options(defer(AssignmentSubmission.text_enc),
                                           defer(AssignmentSubmission.feedback_enc))
                                  .where(AssignmentSubmission.item_id.in_(chunk),
                                         AssignmentSubmission.student_user_id == user_id)):
                subs[sub.item_id] = sub
    due: list[tuple[tuple, dict]] = []
    open_count = 0
    window_start = clock.now - timedelta(days=7)
    window_end = clock.now + timedelta(days=21)
    ovr = at.due_overrides(db, [a.id for a in assignments], user_id) if user_id else {}
    for item in assignments:
        sub = subs.get(item.id)
        status = logic.submission_status(at.effective_due(item.due_at, ovr.get(item.id)),
                                         sub.submitted_at if sub else None, sub.status if sub else None, clock.now)
        open_ = status in ("offen", "ueberfaellig", "zurueckgegeben")
        if open_:
            open_count += 1
        if item.due_at is not None and not window_start <= item.due_at <= window_end and not (
                open_ and item.due_at > window_end - timedelta(days=21)):
            continue
        if not open_ and status != "bewertet":
            # abgegebene Aufgaben nur kurz vor/nach der Frist anzeigen
            if item.due_at is None or item.due_at < clock.now - timedelta(days=2):
                continue
        if status == "bewertet" and (sub is None or sub.feedback_at is None
                                     or sub.feedback_at < clock.now - timedelta(days=7)):
            continue
        ch, spec = channels[item.channel_id]
        key = (0 if open_ else 1, item.due_at or datetime.max, item.id)
        due.append((key, _overview_entry(ch, spec, item, status=status,
                                         status_label=logic.SUBMISSION_LABELS.get(status, status),
                                         overdue=status == "ueberfaellig")))
    new_items.sort(key=lambda x: x[0], reverse=True)
    due.sort(key=lambda x: x[0])
    return [e for _, e in new_items[:10]], [e for _, e in due[:12]], open_count


def _student_channels(db: Session, school, student_id: Optional[str], user_id: Optional[int]
                      ) -> dict[int, tuple[Channel, Optional[logic.ChannelSpec]]]:
    specs = logic.student_specs(school, student_id) if student_id else []
    rows = _ensure_rows(db, specs)
    out = {row.id: (row, spec) for spec in specs if (row := rows.get((spec.kind, spec.ref))) is not None
           and not row.archived}
    if user_id:
        for ch, role in db.execute(select(Channel, ChannelExtraMember.role)
                                   .join(ChannelExtraMember, ChannelExtraMember.channel_id == Channel.id)
                                   .where(ChannelExtraMember.user_id == user_id, Channel.archived.is_(False))):
            if role == EXCLUDED:
                out.pop(ch.id, None)          # aus dem Kursraum ausgetragen
            else:
                out.setdefault(ch.id, (ch, _spec_for(school, ch)))
    return out


def _teacher_overview(db: Session, user: AuthUser, snap: Any, clock: Clock) -> dict[str, Any]:
    school = snap[1]
    specs = logic.teacher_specs(school, user.teacher_id)
    rows = _ensure_rows(db, specs)
    course_specs = [s for s in specs if s.kind == logic.COURSE and (s.kind, s.ref) in rows]
    local_now = logic.utc_to_local(clock.now).strftime("%H:%M")
    day: Optional[date] = None
    found: list[tuple[logic.ChannelSpec, dict]] = []
    cur = clock.today
    for _ in range(14):
        if is_school_day(school, cur)[0]:
            todays = []
            for spec in course_specs:
                res = logic.upcoming_lessons(school, spec.kind, spec.ref, cur, 1, plan_for=clock.plan, now=clock.now)
                todays.extend((spec, lesson) for lesson in res["lessons"])
            if todays and (cur != clock.today or any((x["end_time"] or "99:99") > local_now for _, x in todays)):
                day, found = cur, todays
                break
        cur += timedelta(days=1)
    channel_ids = [rows[(s.kind, s.ref)].id for s in specs if (s.kind, s.ref) in rows]
    extra_ids = set(db.scalars(select(ChannelExtraMember.channel_id).where(
        ChannelExtraMember.user_id == user.id, ChannelExtraMember.role == TEACHER)))
    channel_ids += sorted(extra_ids)
    bound: dict[str, list[dict]] = defaultdict(list)
    if day is not None:
        for chunk in _chunks(sorted(set(channel_ids))):
            for item_id, cid, title, ldate, lid, lper, itype in db.execute(
                    select(ChannelItem.id, ChannelItem.channel_id, ChannelItem.title, ChannelItem.lesson_date,
                           ChannelItem.lesson_id, ChannelItem.lesson_period, ChannelItem.type)
                    .where(ChannelItem.channel_id.in_(chunk), ChannelItem.visibility == "lesson",
                           ChannelItem.lesson_date == day.isoformat())):
                bound[f"{cid}|{logic.lesson_key(ldate, lid or '', lper or 0)}"].append(
                    {"id": item_id, "title": title, "type": itype})
    lessons = []
    for spec, lesson in sorted(found, key=lambda x: (x[1]["effective_period"], x[0].title)):
        ch = rows[(spec.kind, spec.ref)]
        lessons.append({**_lesson_json(lesson), "channel_id": ch.id, "channel_title": spec.title,
                        "items": bound.get(f"{ch.id}|{lesson['key']}", []),
                        "ended": day == clock.today and (lesson["end_time"] or "99:99") <= local_now})
    to_grade = []
    if channel_ids:
        titles = {rows[(s.kind, s.ref)].id: s.title for s in specs if (s.kind, s.ref) in rows}
        class_specs = {rows[(s.kind, s.ref)].id: s for s in specs if (s.kind, s.ref) in rows and s.kind == logic.CLASS}
        stmt = (select(ChannelItem.id, ChannelItem.channel_id, ChannelItem.title, ChannelItem.due_at,
                       ChannelItem.created_by, func.count())
                .join(AssignmentSubmission, AssignmentSubmission.item_id == ChannelItem.id)
                .where(ChannelItem.channel_id.in_(sorted(set(channel_ids))),
                       AssignmentSubmission.status.in_(OPEN_SUBMISSIONS))
                .group_by(ChannelItem.id, ChannelItem.channel_id, ChannelItem.title, ChannelItem.due_at,
                          ChannelItem.created_by))
        missing_titles = set()
        for item_id, cid, title, due_at, created_by, n in db.execute(stmt):
            cspec = class_specs.get(cid)
            if cspec is not None and created_by != user.id and not (    # Klassenraum: nur eigene Aufgaben
                    created_by is None and (cspec.class_teacher == user.teacher_id or cid in extra_ids)):
                continue
            if cid not in titles:
                missing_titles.add(cid)
            to_grade.append({"channel_id": cid, "item_id": item_id, "title": title, "due_at": iso(due_at),
                             "count": int(n)})
        if missing_titles:
            for ch in db.scalars(select(Channel).where(Channel.id.in_(sorted(missing_titles)))):
                spec = _spec_for(school, ch)
                titles[ch.id] = spec.title if spec else ch.title
        for entry in to_grade:
            entry["channel_title"] = titles.get(entry["channel_id"], "")
        to_grade.sort(key=lambda e: (e["due_at"] or "9999", e["title"]))
    return {"day": day.isoformat() if day else None, "is_today": day == clock.today,
            "lessons": lessons, "to_grade": to_grade[:20],
            "to_grade_total": sum(e["count"] for e in to_grade)}


def _lesson_json(lesson: dict[str, Any]) -> dict[str, Any]:
    out = dict(lesson)
    out["release_at"] = iso(lesson.get("release_at"))
    return out


@router.get("/channels/overview")
def channels_overview(student_id: Optional[str] = Query(None, max_length=40), user: AuthUser = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    """Startseite: Schüler/innen neues Material + fällige Aufgaben; Lehrkräfte heutige Stunden mit gebundenem
    Material + Abgaben zum Bewerten; Eltern (``?student_id=``) Titel/Frist/Status der Aufgaben des Kindes
    (volljährig nur mit Einwilligung, sonst ``restricted``)."""
    snap = snapshot()
    school = snap[1]
    clock = Clock(snap)
    if not _uses_channels(user):
        kids = list(getattr(user, "student_ids", None) or [])
        if getattr(user, "role", "") != "eltern" or not kids:
            raise HTTPException(403, "Keine Berechtigung für Kursräume")
        sid = student_id or (kids[0] if len(kids) == 1 else None)
        idx = logic.index_for(school)
        children = [{"id": k, "name": idx.students[k].name if k in idx.students else k,
                     "class_id": idx.students[k].class_id if k in idx.students else None} for k in kids]
        out: dict[str, Any] = {"role": "parent", "now": iso(clock.now), "children": children, "student_id": sid,
                               "due": [], "open_assignments": 0, "restricted": False, "has_account": False}
        if sid is None:
            return out
        if sid not in kids:
            raise HTTPException(403, "Keine Berechtigung für diese Schülerin/diesen Schüler")
        account = db.scalars(select(User).where(User.student_id == sid, User.role == "schueler",
                                                User.active.is_(True)).order_by(User.id)).first()
        if not pa.parent_may_see(db, sid, pa.AREA_CHANNELS, school=school):
            out["restricted"] = True       # volljährig ohne Einwilligung: keine Kursraum-Daten
            return out
        channels = _student_channels(db, school, sid, account.id if account else None)
        _, due, n_open = _pupil_lists(db, account.id if account else None, channels, clock, with_new=False)
        out.update({"due": due, "open_assignments": n_open, "has_account": account is not None})
        return out
    is_teacher = bool(user.teacher_id and has(user, "channels.manage"))
    role = "teacher" if is_teacher else "student" if user.student_id else "supervisor" if _is_supervisor(user) else "none"
    out = {"role": role, "now": iso(clock.now), "no_teacher_link": _no_teacher_link(user)}
    if is_teacher:
        out["teacher"] = _teacher_overview(db, user, snap, clock)
    if user.student_id:
        channels = _student_channels(db, school, user.student_id, user.id)
        new_items, due, n_open = _pupil_lists(db, user.id, channels, clock, with_new=True)
        out["student"] = {"new_items": new_items, "due": due, "open_assignments": n_open}
    return out


# =========================================================================== Kanäle
def _matches(entry: dict[str, Any], q: str) -> bool:
    hay = " ".join(str(x) for x in (entry["title"], entry["subtitle"], entry["ref"] or "", " ".join(entry["classes"]),
                                    entry.get("subject_name") or "", " ".join(entry["teachers"]))).casefold()
    return all(part in hay for part in q.casefold().split())


@router.get("/channels")
def list_channels(q: str = Query("", max_length=100), kind: Optional[Literal["course", "class", "custom"]] = None,
                  all: bool = Query(False, description="Aufsicht: alle Kursräume der Schule"),  # noqa: A002
                  archived: bool = Query(False, description="auch archivierte Kursräume"),
                  student_id: Optional[str] = Query(None, max_length=40, description="Eltern: Kind"),
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eigene Kursräume (Lehrkraft: eigene Kursteile + Klassen, Schüler/in: besuchte Kursteile + Klasse,
    Zusatzmitgliedschaften); Schulleitung/Admin mit ``?all=1`` alle Kursräume (nur lesend); Eltern die Kursräume
    eines Kindes (``?student_id=``, sonst des ersten). ``notice: "no_teacher_link"`` = Lehrkraft-Konto ohne
    Zuordnung."""
    _need_channels(user)
    snap = snapshot()
    school = snap[1]
    clock = Clock(snap)
    if not _uses_channels(user):
        return _parent_channel_list(db, user, student_id, q, kind, clock)
    sup = _is_supervisor(user)
    show_all = bool(all and sup)
    manage = has(user, "channels.manage")
    own_teacher = logic.teacher_specs(school, user.teacher_id) if manage and user.teacher_id else []
    own_student = logic.student_specs(school, user.student_id) if user.student_id else []
    specs = logic.all_specs(school) if show_all else [*own_teacher, *own_student]
    rows = _ensure_rows(db, specs)
    teacher_keys = {(s.kind, s.ref) for s in own_teacher}
    student_keys = {(s.kind, s.ref) for s in own_student}
    extras = {cid: role for cid, role in db.execute(
        select(ChannelExtraMember.channel_id, ChannelExtraMember.role).where(ChannelExtraMember.user_id == user.id))}
    entries: dict[int, tuple[Channel, Optional[logic.ChannelSpec], str]] = {}
    for spec in specs:
        key = (spec.kind, spec.ref)
        ch = rows.get(key)
        if ch is None or ch.id in entries:
            continue
        role = TEACHER if key in teacher_keys else STUDENT if key in student_keys else None
        extra = extras.get(ch.id)
        if extra == EXCLUDED and role == STUDENT:
            role = None
        if extra == TEACHER and manage:
            role = TEACHER
        elif role is None and extra in (TEACHER, STUDENT):
            role = STUDENT
        if role is None and show_all:
            role = SUPERVISOR
        if role:
            entries[ch.id] = (ch, spec, role)
    others = [cid for cid, r in extras.items() if cid not in entries and r != EXCLUDED]
    stmt = None
    if show_all:
        stmt = select(Channel).where(or_(Channel.kind == logic.CUSTOM, Channel.id.in_(others) if others else False))
    elif others:
        stmt = select(Channel).where(Channel.id.in_(others))
    if stmt is not None:
        for ch in db.scalars(stmt):
            if ch.id in entries:
                continue
            spec = _spec_for(school, ch)
            role = _role_for(db, user, ch, spec, school, extra=extras.get(ch.id))
            if role:
                entries[ch.id] = (ch, spec, role)
    if show_all:  # verwaiste Kurs-/Klassenkanäle (Kurs/Klasse gibt es nicht mehr), damit nichts verloren geht
        known = set(entries)
        for ch in db.scalars(select(Channel).where(Channel.kind.in_((logic.COURSE, logic.CLASS)))):
            if ch.id not in known and _spec_for(school, ch) is None:
                entries[ch.id] = (ch, None, SUPERVISOR)
    selected = [(ch, spec, role) for ch, spec, role in entries.values()
                if (archived or not ch.archived) and (kind is None or ch.kind == kind)]
    stats = _channel_stats(db, user, selected, clock)
    out = [_channel_out(ch, spec, role, school, stats.get(ch.id)) for ch, spec, role in selected]
    if q.strip():
        out = [e for e in out if _matches(e, q.strip())]
    order = {logic.COURSE: 0, logic.CLASS: 1, logic.CUSTOM: 2}
    out.sort(key=lambda e: (e["archived"], order.get(e["kind"], 3), logic._natural(e["title"]), e["id"]))
    return {"channels": out, "supervisor": sup, "can_create": sup, "all": show_all, "count": len(out),
            "now": iso(clock.now), "notice": "no_teacher_link" if _no_teacher_link(user) else None,
            "notice_text": NO_TEACHER_LINK if _no_teacher_link(user) else None}


def _parent_channel_list(db: Session, user: AuthUser, student_id: Optional[str], q: str, kind: Optional[str],
                         clock: Clock) -> dict:
    """Elternansicht: Kursräume eines Kindes (nur lesen; volljährig nur mit Einwilligung)."""
    school = clock.school
    kids = list(dict.fromkeys(getattr(user, "student_ids", None) or []))
    if student_id and student_id not in kids:
        raise HTTPException(403, "Keine Berechtigung für diese Schülerin/diesen Schüler")
    idx = logic.index_for(school)
    children = [{"id": k, "name": idx.students[k].name if k in idx.students else k,
                 "class_id": idx.students[k].class_id if k in idx.students else None,
                 "allowed": pa.parent_may_see(db, k, pa.AREA_CHANNELS, school=school)} for k in kids]
    sel = student_id or (kids[0] if kids else None)
    out: list[dict[str, Any]] = []
    restricted = False
    if sel is not None:
        restricted = not next(c["allowed"] for c in children if c["id"] == sel)
        if not restricted:
            uid = _account_of(db, sel)
            chans = _student_channels(db, school, sel, uid)
            entries = [(ch, spec, PARENT) for ch, spec in chans.values() if kind is None or ch.kind == kind]
            stats = _channel_stats(db, user, entries, clock, pupil_uid=uid)
            out = [_channel_out(ch, spec, PARENT, school, stats.get(ch.id)) for ch, spec, _ in entries]
            if q.strip():
                out = [e for e in out if _matches(e, q.strip())]
            order = {logic.COURSE: 0, logic.CLASS: 1, logic.CUSTOM: 2}
            out.sort(key=lambda e: (order.get(e["kind"], 3), logic._natural(e["title"]), e["id"]))
    return {"channels": out, "supervisor": False, "can_create": False, "all": False, "count": len(out),
            "now": iso(clock.now), "notice": None, "parent": True, "children": children, "student_id": sel,
            "restricted": restricted}


@router.post("/channels", status_code=201)
def create_channel(body: ChannelIn, request: Request, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Eigenen Kursraum anlegen (AG, Projekt, Fachschaft) – nur Schulleitung/Admin; Ersteller/in wird Lehrende/r."""
    _need_channels(user)
    if not _is_supervisor(user):
        raise HTTPException(403, "Eigene Kursräume legt die Schulleitung an")
    title = logic.clean_name(body.title, 200)
    if not title:
        raise HTTPException(422, "Bitte einen Titel angeben")
    ch = Channel(kind=logic.CUSTOM, ref=None, title=title, description=logic.clean_text(body.description, 2000),
                 settings={"students_can_post": body.students_can_post, "students_can_reply": body.students_can_reply},
                 archived=False, created_by=user.id, created_at=utcnow())
    db.add(ch)
    db.flush()
    db.add(ChannelExtraMember(channel_id=ch.id, user_id=user.id, role=TEACHER, added_by=user.id, created_at=utcnow()))
    audit(db, user, "channel.create", f"channel:{ch.id}", {"kind": logic.CUSTOM}, ip=client_ip(request))
    db.commit()
    snap = snapshot()
    return _channel_out(ch, None, TEACHER, snap[1])


@router.get("/channels/{channel_id}")
def get_channel(channel_id: int, student_id: Optional[str] = Query(None, max_length=40, description="Eltern: Kind"),
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Kursraum mit Ordnern und Material (Teilnehmende/Eltern: nur Freigegebenes) und den eigenen Rechten."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    folders = _folders(db, ctx.ch.id)
    hidden = clock.folder_states(folders)
    last_seen = db.scalar(select(ChannelRead.last_seen_at).where(ChannelRead.channel_id == ctx.ch.id,
                                                                 ChannelRead.user_id == user.id))
    rows = _load_items(db, [ctx.ch.id])
    stats = _channel_stats(db, user, [(ctx.ch, ctx.spec, ctx.role)], clock, pupil_uid=ctx.pupil_uid).get(ctx.ch.id)
    idx = logic.index_for(ctx.school)
    return {
        "channel": _channel_out(ctx.ch, ctx.spec, ctx.role, ctx.school, stats),
        "permissions": _permissions_out(ctx),
        "child": {"id": ctx.child, "name": idx.students[ctx.child].name if ctx.child in idx.students else ctx.child}
        if ctx.parent else None,
        "children": [{"id": k, "name": idx.students[k].name if k in idx.students else k} for k in ctx.children],
        "folders": _folders_out(ctx, folders, hidden, clock),
        "items": _items_out(db, ctx, rows, hidden, clock, last_seen),
        "last_seen_at": iso(last_seen),
        "next_release_at": iso(_next_release(rows, hidden, clock)),
        "now": iso(clock.now),
        "limits": {"max_body": MAX_BODY, "max_attachments": MAX_ATTACHMENTS, "max_upload_items": MAX_UPLOAD_ITEMS,
                   "max_post": MAX_POST, "max_submission_text": MAX_SUBMISSION_TEXT, "max_grade": MAX_GRADE},
    }


@router.patch("/channels/{channel_id}")
def patch_channel(channel_id: int, body: ChannelPatch, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    """Beschreibung/Pinnwand-Einstellungen (Lehrende); Titel eigener Kursräume, Archivieren (Schulleitung/Admin)."""
    ctx = _ctx(db, user, channel_id)
    sup = _is_supervisor(user)
    fields = body.model_fields_set
    if body.archived:
        raise HTTPException(422, "Kursräume werden nicht mehr archiviert")
    if fields - {"archived"} and not ctx.teacher:
        raise HTTPException(403, "Nur Lehrende dieses Kursraums dürfen das")
    if "archived" in fields and not sup:
        raise HTTPException(403, "Archivieren darf nur die Schulleitung")
    if fields - {"archived"} and ctx.ch.archived and not (fields == {"archived"}):
        if body.archived is not False:
            raise HTTPException(409, "Der Kursraum ist archiviert – Änderungen sind nicht mehr möglich")
    changes: dict[str, Any] = {}
    if body.title is not None:
        if ctx.ch.kind != logic.CUSTOM:
            raise HTTPException(422, "Kurs- und Klassenkursräume heißen wie Kurs bzw. Klasse")
        title = logic.clean_name(body.title, 200)
        if not title:
            raise HTTPException(422, "Bitte einen Titel angeben")
        if title != ctx.ch.title:
            ctx.ch.title = title
            changes["title"] = True
    if body.description is not None:
        text = logic.clean_text(body.description, 2000)
        if text != (ctx.ch.description or ""):
            ctx.ch.description = text
            changes["description"] = True
    settings = {**(ctx.ch.settings or {})}
    for key in ("students_can_post", "students_can_reply", "progress_parents"):
        value = getattr(body, key)
        if value is not None and bool(ctx.ch.setting(key)) != value:
            settings[key] = value
            changes[key] = value
    if settings != (ctx.ch.settings or {}):
        ctx.ch.settings = settings
    if body.archived is not None and bool(ctx.ch.archived) != body.archived:
        ctx.ch.archived = body.archived
        changes["archived"] = body.archived
    if changes:
        ctx.ch.updated_at = utcnow()
        audit(db, user, "channel.archive" if "archived" in changes else "channel.update", f"channel:{ctx.ch.id}",
              changes, ip=client_ip(request))
        db.commit()
        _notify(db, ctx)
    return _channel_out(ctx.ch, ctx.spec, ctx.role, ctx.school)


@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, request: Request, force: bool = False, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Eigenen Kursraum löschen (Schulleitung/Admin; mit Inhalt nur mit ``?force=1``). Kurs-/Klassenkursräume
    werden archiviert, nicht gelöscht."""
    ctx = _ctx(db, user, channel_id)
    if not _is_supervisor(user):
        raise HTTPException(403, "Kursräume löscht nur die Schulleitung")
    if ctx.ch.kind != logic.CUSTOM:
        raise HTTPException(409, "Kurs- und Klassenkursräume können nur archiviert werden")
    items = list(db.scalars(select(ChannelItem).where(ChannelItem.channel_id == ctx.ch.id),
                            execution_options={"include_trashed": True}))
    posts = int(db.scalar(select(func.count()).select_from(ChannelPost).where(ChannelPost.channel_id == ctx.ch.id))
                or 0)
    if (items or posts) and not force:
        raise HTTPException(409, {"message": f"Der Kursraum enthält {len(items)} Materialien und {posts} Beiträge. "
                                  "Wirklich alles löschen?", "items": len(items), "posts": posts})
    member_ids = _member_user_ids(db, ctx.ch, ctx.spec, ctx.school)
    _delete_item_rows(db, items)
    for post_id in list(db.scalars(select(ChannelPost.id).where(ChannelPost.channel_id == ctx.ch.id))):
        files.delete_for_ref(db, REF_POST, post_id, hard=True)
    audit(db, user, "channel.delete", f"channel:{ctx.ch.id}", {"items": len(items), "posts": posts},
          ip=client_ip(request))
    db.delete(ctx.ch)
    db.commit()
    bus.publish("change", {"version": None, "scope": ["channels", f"channel:{channel_id}:"], "dates": []},
                user_ids=member_ids | {user.id})
    return {"deleted": channel_id}


@router.post("/channels/{channel_id}/seen")
def mark_seen(channel_id: int, student_id: Optional[str] = Query(None, max_length=40),
              user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Besuch merken (Material/Beiträge danach nicht mehr „neu“)."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    now = utcnow()
    row = db.scalar(select(ChannelRead).where(ChannelRead.channel_id == ctx.ch.id, ChannelRead.user_id == user.id))
    if row is None:
        db.add(ChannelRead(channel_id=ctx.ch.id, user_id=user.id, last_seen_at=now))
    else:
        row.last_seen_at = now
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    bus.publish("change", {"version": None, "scope": ["channels"], "dates": []}, user_ids={user.id})
    return {"last_seen_at": iso(now)}


# =========================================================================== Teilnehmende
def _child_accounts(db: Session, student_ids: Iterable[str]) -> dict[str, User]:
    out: dict[str, User] = {}
    for chunk in _chunks(sorted(set(student_ids))):
        for u in db.scalars(select(User).where(User.student_id.in_(chunk), User.role == "schueler",
                                               User.active.is_(True))):
            out.setdefault(u.student_id, u)
    return out



def _can_manage_members(ctx: Ctx) -> bool:
    """Lehrende des Kursraums (Fach-/Klassenlehrkräfte) und die Aufsicht (Schulleitung/Admin)."""
    return ctx.teacher or _is_supervisor(ctx.user)


def _parents_of(db: Session, student_ids: list[str]) -> dict[str, list[tuple[int, str]]]:
    """Kind → [(Eltern-Konto, Name)] (nur aktive Konten)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for chunk in _chunks(sorted(set(student_ids))):
        for sid, uid, dn, un in db.execute(
                select(ParentLink.student_id, User.id, User.display_name, User.username)
                .join(User, User.id == ParentLink.parent_user_id)
                .where(ParentLink.student_id.in_(chunk), User.active.is_(True))):
            out.setdefault(sid, []).append((uid, dn or un))
    return out


@router.get("/channels/{channel_id}/members")
def list_members(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Lehrende, Teilnehmende (Stundenplan + eingetragen), ausgetragene Schüler/innen und Eltern mit Zugang
    (nicht für Eltern)."""
    ctx = _ctx(db, user, channel_id)
    if ctx.parent:
        raise HTTPException(403, "Die Teilnehmendenliste sehen Eltern nicht")
    idx = logic.index_for(ctx.school)
    spec = ctx.spec
    staff = ctx.staff_view
    teacher_ids = list(spec.teacher_ids) if spec else []
    student_ids = logic.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "") if spec else []
    accounts_t: dict[str, int] = {}
    if staff:
        for chunk in _chunks(teacher_ids):
            for uid, tid in db.execute(select(User.id, User.teacher_id).where(User.teacher_id.in_(chunk),
                                                                             User.active.is_(True))):
                accounts_t.setdefault(tid, uid)
    student_accounts = _child_accounts(db, student_ids) if staff else {}
    extra_rows = db.execute(select(ChannelExtraMember, User.display_name, User.username, User.role, User.student_id)
                            .join(User, User.id == ChannelExtraMember.user_id)
                            .where(ChannelExtraMember.channel_id == ctx.ch.id)
                            .order_by(ChannelExtraMember.role, User.display_name)).all()
    excluded_uids = {m.user_id for m, *_ in extra_rows if m.role == EXCLUDED}
    teachers = []
    for tid in teacher_ids:
        entry: dict[str, Any] = {"id": tid, "name": idx.teacher_name(tid),
                                 "class_teacher": bool(spec and spec.class_teacher == tid)}
        if staff:
            entry["has_account"] = tid in accounts_t
        teachers.append(entry)
    students = []
    for sid in sorted(student_ids, key=lambda s: (idx.students[s].class_id, idx.students[s].name)
                      if s in idx.students else ("", s)):
        st = idx.students.get(sid)
        acc = student_accounts.get(sid)
        if acc is not None and acc.id in excluded_uids:
            continue
        entry = {"id": sid if staff else None, "name": st.name if st else sid, "class_id": st.class_id if st else None}
        if staff:
            entry["has_account"] = acc is not None
            entry["user_id"] = acc.id if acc else None
        students.append(entry)
    can_manage = _can_manage_members(ctx) and not ctx.ch.archived
    extra = []
    excluded = []
    for m, dn, un, urole, sid in extra_rows:
        e = {"user_id": m.user_id if staff or _is_supervisor(user) else None, "name": dn or un, "role": m.role,
             "role_label": ROLE_LABELS.get(m.role, m.role), "account_role": urole if staff else None,
             "added_at": iso(m.created_at), "self": m.user_id == user.id,
             "creator": m.user_id == ctx.ch.created_by}
        if staff:
            e["class_id"] = idx.students[sid].class_id if sid and sid in idx.students else None
        (excluded if m.role == EXCLUDED else extra).append(e)
    # Eltern mit Zugang (Kinder = Teilnehmende aus Stundenplan + eingetragene Schüler/innen)
    parents: list[dict[str, Any]] = []
    if staff:
        kid_ids = [s["id"] for s in students if s.get("id")]
        kid_ids += [sid for m, _dn, _un, urole, sid in extra_rows
                    if m.role == STUDENT and urole == "schueler" and sid]
        seen: dict[int, dict[str, Any]] = {}
        for sid, plist in _parents_of(db, kid_ids).items():
            if not pa.parent_may_see(db, sid, pa.AREA_CHANNELS, school=ctx.school):
                continue                  # volljährig ohne Einwilligung (Elternzugriff)
            kid = idx.students.get(sid)
            for uid, name in plist:
                p = seen.setdefault(uid, {"user_id": uid, "name": name, "children": []})
                p["children"].append(kid.name if kid else sid)
        parents = sorted(seen.values(), key=lambda p: p["name"])
    return {"teachers": teachers, "students": students, "extra": extra, "excluded": excluded if staff else [],
            "parents": parents,
            "counts": {"teachers": len(teachers) + sum(1 for e in extra if e["role"] == TEACHER),
                       "students": len(students) + sum(1 for e in extra if e["role"] == STUDENT),
                       "parents": len(parents)},
            "can_manage_members": can_manage, "can_add_teachers": _is_supervisor(user) and not ctx.ch.archived,
            "creator_id": ctx.ch.created_by}


@router.get("/channels/{channel_id}/member-candidates")
def member_candidates(channel_id: int, q: str = Query("", max_length=100), role: Literal["student", "teacher"] = "student",
                      user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Konten zum Eintragen suchen (Name, Benutzername oder Klasse). Lehrende: Schüler/innen; Aufsicht auch Lehrende."""
    ctx = _ctx(db, user, channel_id)
    if not _can_manage_members(ctx):
        raise HTTPException(403, "Teilnehmende tragen die Lehrenden dieses Kursraums ein")
    if role == TEACHER and not _is_supervisor(user):
        raise HTTPException(403, "Lehrende trägt die Schulleitung ein")
    term = q.strip().lower()
    if len(term) < 2:
        return {"candidates": []}
    idx = logic.index_for(ctx.school)
    roles = ["schueler"] if role == STUDENT else ["lehrer", "schulleitung", "admin", "planer"]
    present = set(db.scalars(select(ChannelExtraMember.user_id).where(ChannelExtraMember.channel_id == ctx.ch.id,
                                                                      ChannelExtraMember.role != EXCLUDED)))
    dyn = set(logic.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "")) if ctx.spec else set()
    out = []
    like = f"%{term}%"
    stmt = (select(User).where(User.active.is_(True), User.role.in_(roles))
            .where(or_(func.lower(User.display_name).like(like), func.lower(User.username).like(like)))
            .order_by(User.display_name).limit(60))
    rows = list(db.scalars(stmt))
    if role == STUDENT:   # auch nach Klasse suchen („7b“)
        cls_ids = [s.id for c, members in idx.students_by_class.items() if c.lower() == term for s in members]
        for chunk in _chunks(cls_ids):
            rows += list(db.scalars(select(User).where(User.active.is_(True), User.role == "schueler",
                                                       User.student_id.in_(chunk))))
    done: set[int] = set()
    for u in rows:
        if u.id in done:
            continue
        done.add(u.id)
        st = idx.students.get(u.student_id) if u.student_id else None
        out.append({"user_id": u.id, "name": u.display_name or u.username, "username": u.username,
                    "account_role": u.role, "class_id": st.class_id if st else None,
                    "member": u.id in present or (u.student_id in dyn if u.student_id else False)})
        if len(out) >= 40:
            break
    return {"candidates": out}


@router.post("/channels/{channel_id}/members", status_code=201)
def add_members(channel_id: int, body: MembersIn, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Mitglieder eintragen: Lehrende des Kursraums tragen Schüler/innen ein (deren Eltern sehen den Kursraum dann
    mit), die Aufsicht (Schulleitung/Admin) zusätzlich Lehrende. Ausgetragene Schüler/innen werden wieder Mitglied."""
    ctx = _ctx(db, user, channel_id)
    sup = _is_supervisor(user)
    if not _can_manage_members(ctx):
        raise HTTPException(403, "Teilnehmende tragen die Lehrenden dieses Kursraums ein")
    if body.role == TEACHER and not sup:
        raise HTTPException(403, "Lehrende trägt die Schulleitung ein")
    if ctx.ch.archived:
        raise HTTPException(409, "Der Kursraum ist archiviert")
    dyn = set(logic.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "")) if ctx.spec else set()
    added, updated = [], []
    for uid in dict.fromkeys(body.user_ids):
        target = db.get(User, uid)
        if target is None or not target.active:
            raise HTTPException(404, f"Konto {uid} nicht gefunden")
        name = target.display_name or target.username
        perms = permissions_for(target.role, bool(target.adult))
        if body.role == TEACHER and "channels.manage" not in perms:
            raise HTTPException(422, f"{name}: Dieses Konto kann nicht Lehrende/r sein (Recht „Kursräume verwalten“ "
                                "fehlt)")
        if target.role == "eltern":
            raise HTTPException(422, f"{name}: Eltern sehen Kursräume automatisch über ihre Kinder")
        if body.role == STUDENT and not sup and target.role != "schueler":
            raise HTTPException(422, f"{name}: Lehrkräfte tragen nur Schüler/innen ein")
        if "channels.use" not in perms and "channels.manage" not in perms:
            raise HTTPException(422, f"{name}: Dieses Konto kann Kursräume nicht nutzen")
        row = db.scalar(select(ChannelExtraMember).where(ChannelExtraMember.channel_id == ctx.ch.id,
                                                         ChannelExtraMember.user_id == uid))
        if row is not None and row.user_id == ctx.ch.created_by and body.role != TEACHER:
            raise HTTPException(409, "Wer den Kursraum erstellt hat, bleibt Lehrende/r")
        if row is not None and row.role == EXCLUDED and target.student_id in dyn and body.role == STUDENT:
            db.delete(row)              # aus dem Stundenplan wieder aufnehmen
            updated.append(uid)
            continue
        if row is None:
            if body.role == STUDENT and target.student_id and target.student_id in dyn:
                continue                # ist schon über den Stundenplan Mitglied
            db.add(ChannelExtraMember(channel_id=ctx.ch.id, user_id=uid, role=body.role, added_by=user.id,
                                      created_at=utcnow()))
            added.append(uid)
        elif row.role != body.role:
            if row.role == TEACHER and not sup:
                raise HTTPException(403, "Lehrende trägt die Schulleitung aus")
            row.role = body.role
            updated.append(uid)
    if added or updated:
        audit(db, user, "channel.member_add", f"channel:{ctx.ch.id}",
              {"added": added, "updated": updated, "role": body.role, "self": user.id in added + updated},
              ip=client_ip(request))
        db.commit()
        _notify(db, ctx, extra_ids=added + updated + _parent_ids_of_users(db, added + updated))
    return {"added": added, "updated": updated}


def _parent_ids_of_users(db: Session, user_ids: list[int]) -> list[int]:
    sids = [sid for sid in db.scalars(select(User.student_id).where(User.id.in_(user_ids or [-1]))) if sid]
    return [uid for plist in _parents_of(db, sids).values() for uid, _ in plist]


@router.delete("/channels/{channel_id}/members/{user_id}")
def remove_member(channel_id: int, user_id: int, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    """Mitglied austragen: Lehrende tragen Schüler/innen aus (auch solche aus dem Stundenplan), die Aufsicht auch
    Lehrende; jede/r darf sich selbst austragen – außer, wer den Kursraum erstellt hat (kein Aussperren)."""
    ctx = _ctx(db, user, channel_id)
    sup = _is_supervisor(user)
    manage = _can_manage_members(ctx)
    if not (manage or user_id == user.id):
        raise HTTPException(403, "Mitglieder tragen die Lehrenden dieses Kursraums aus")
    if user_id == ctx.ch.created_by:
        raise HTTPException(409, "Wer den Kursraum erstellt hat, kann ihn nicht verlassen und nicht ausgetragen werden")
    row = db.scalar(select(ChannelExtraMember).where(ChannelExtraMember.channel_id == ctx.ch.id,
                                                     ChannelExtraMember.user_id == user_id))
    target = db.get(User, user_id)
    dyn_student = bool(ctx.spec and target is not None and target.student_id and target.role == "schueler"
                       and logic.is_channel_student(ctx.school, ctx.ch.kind, ctx.ch.ref or "", target.student_id))
    if row is None and not dyn_student:
        raise HTTPException(404, "Kein Mitglied dieses Kursraums")
    if row is not None and row.role == TEACHER and not (sup or user_id == user.id):
        raise HTTPException(403, "Lehrende trägt die Schulleitung aus")
    if row is not None and row.role == TEACHER and ctx.ch.kind == logic.CUSTOM:
        others = int(db.scalar(select(func.count()).select_from(ChannelExtraMember).where(
            ChannelExtraMember.channel_id == ctx.ch.id, ChannelExtraMember.role == TEACHER,
            ChannelExtraMember.user_id != user_id)) or 0)
        if not others:
            raise HTTPException(409, "Ein eigener Kursraum braucht mindestens eine/n Lehrende/n")
    old_role = row.role if row is not None else STUDENT
    if dyn_student:
        # Schüler/in aus dem Stundenplan: als „ausgetragen“ merken (sonst wäre er/sie sofort wieder Mitglied)
        if row is None:
            db.add(ChannelExtraMember(channel_id=ctx.ch.id, user_id=user_id, role=EXCLUDED, added_by=user.id,
                                      created_at=utcnow()))
        elif row.role == EXCLUDED:
            raise HTTPException(409, "Bereits ausgetragen")
        else:
            row.role = EXCLUDED
    else:
        db.delete(row)
    audit(db, user, "channel.member_remove", f"channel:{ctx.ch.id}", {"user_id": user_id, "role": old_role},
          ip=client_ip(request))
    db.commit()
    _notify(db, ctx, extra_ids=[user_id, *_parent_ids_of_users(db, [user_id])])
    return {"removed": user_id}


@router.delete("/channels/{channel_id}/excluded/{user_id}")
def readmit_member(channel_id: int, user_id: int, request: Request, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Ausgetragene/n Schüler/in aus dem Stundenplan wieder aufnehmen."""
    ctx = _ctx(db, user, channel_id)
    if not _can_manage_members(ctx):
        raise HTTPException(403, "Mitglieder verwalten die Lehrenden dieses Kursraums")
    row = db.scalar(select(ChannelExtraMember).where(ChannelExtraMember.channel_id == ctx.ch.id,
                                                     ChannelExtraMember.user_id == user_id,
                                                     ChannelExtraMember.role == EXCLUDED))
    if row is None:
        raise HTTPException(404, "Nicht ausgetragen")
    db.delete(row)
    audit(db, user, "channel.member_readmit", f"channel:{ctx.ch.id}", {"user_id": user_id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx, extra_ids=[user_id, *_parent_ids_of_users(db, [user_id])])
    return {"readmitted": user_id}


# =========================================================================== Ordner
def _folder_out(f: ChannelFolder) -> dict[str, Any]:
    return {"id": f.id, "parent_id": f.parent_id, "name": f.name, "position": f.position, "hidden": bool(f.hidden),
            "visibility": f.effective_visibility, "visible_from": iso(f.visible_from)}


def _folder_fields(ctx: Ctx, body: Any, clock: Clock) -> Optional[dict[str, Any]]:
    """Freigabe-Felder eines Ordners aus ``visibility`` (neu) bzw. ``hidden`` (alt); ``None`` = keine Änderung."""
    fields = body.model_fields_set
    if "visibility" in fields and body.visibility is not None:
        return _visibility_fields(ctx, body.visibility, body.visible_from, body.lesson, clock)
    if "hidden" in fields and body.hidden is not None:
        return _visibility_fields(ctx, "hidden" if body.hidden else "visible", None, None, clock)
    return None


def _unique_folder_name(name: str, taken: set[str]) -> str:
    if name.casefold() not in taken:
        taken.add(name.casefold())
        return name
    n = 2
    while f"{name} ({n})".casefold() in taken:
        n += 1
    out = f"{name} ({n})"
    taken.add(out.casefold())
    return out


@router.post("/channels/{channel_id}/folders", status_code=201)
def create_folder(channel_id: int, body: FolderIn, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    folders = _folders(db, ctx.ch.id)
    if len(folders) >= MAX_FOLDERS:
        raise HTTPException(409, f"Höchstens {MAX_FOLDERS} Ordner je Kursraum")
    parent = _get_folder(db, ctx, body.parent_id)
    if parent is not None and _folder_depth({f.id: f for f in folders}, parent.id) >= MAX_FOLDER_DEPTH:
        raise HTTPException(422, f"Ordner lassen sich höchstens {MAX_FOLDER_DEPTH} Ebenen tief verschachteln")
    name = logic.clean_name(body.name, 120)
    if not name:
        raise HTTPException(422, "Bitte einen Ordnernamen angeben")
    vis = _folder_fields(ctx, body, clock) or _visibility_fields(ctx, "visible", None, None, clock)
    folder = ChannelFolder(channel_id=ctx.ch.id, parent_id=parent.id if parent else None, name=name,
                           position=_next_position(db, ctx.ch.id, parent.id if parent else None, ChannelFolder),
                           hidden=False, created_by=user.id, created_at=utcnow())
    _apply_folder_visibility(folder, vis, clock.now)
    if folder.visibility == "visible":
        folder.visible_from = None
    db.add(folder)
    db.flush()
    if folder.effective_visibility != "visible":
        audit(db, user, "channel_folder.release", f"channel_folder:{folder.id}",
              {"channel_id": ctx.ch.id, "visibility": folder.effective_visibility}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx, teachers_only=folder.effective_visibility != "visible")
    return _folder_out(folder)


@router.post("/channels/{channel_id}/folders/tree", status_code=201)
def create_folder_tree(channel_id: int, body: FolderTreeIn, request: Request, user: AuthUser = Depends(current_user),
                       db: Session = Depends(get_db)) -> dict:
    """Ordner-Upload (ganzer Ordner vom Computer): legt die Ordnerstruktur an und liefert ``{pfad: ordner_id}`` für
    das anschließende Hochladen der Dateien (``POST …/items/files`` mit ``folder_id``). Die obersten Ordner sind neu
    (gleichnamige werden „Name (2)“) und tragen die gewählte Sichtbarkeit; Unterordner sind sichtbar."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    parent = _get_folder(db, ctx, body.parent_id)
    folders = _folders(db, ctx.ch.id)
    by_id = {f.id: f for f in folders}
    base_depth = _folder_depth(by_id, parent.id) if parent else 0
    paths: dict[str, list[str]] = {}
    for raw in body.paths:
        parts = [logic.clean_name(p, 120) for p in str(raw).replace("\\", "/").split("/")]
        if any(p in (".", "..") for p in parts):
            raise HTTPException(422, "Ungültiger Ordnerpfad")
        parts = [p for p in parts if p]
        if not parts:
            continue
        if base_depth + len(parts) > MAX_FOLDER_DEPTH:
            raise HTTPException(422, f"Ordner lassen sich höchstens {MAX_FOLDER_DEPTH} Ebenen tief verschachteln – "
                                f"„{'/'.join(parts)}“ ist zu tief")
        for i in range(1, len(parts) + 1):
            paths.setdefault("/".join(parts[:i]), parts[:i])
    if not paths:
        raise HTTPException(422, "Bitte mindestens einen Ordner angeben")
    if len(folders) + len(paths) > MAX_FOLDERS:
        raise HTTPException(409, f"Höchstens {MAX_FOLDERS} Ordner je Kursraum")
    vis = _visibility_fields(ctx, body.visibility, body.visible_from, body.lesson, clock)
    visible = _visibility_fields(ctx, "visible", None, None, clock)
    parent_id = parent.id if parent else None
    taken = {f.name.casefold() for f in folders if f.parent_id == parent_id}
    created: dict[str, ChannelFolder] = {}
    now = utcnow()
    roots = 0
    for key in sorted(paths, key=lambda k: (k.count("/"), k)):
        parts = paths[key]
        if len(parts) == 1:
            pid, name = parent_id, _unique_folder_name(parts[0], taken)
            pos = _next_position(db, ctx.ch.id, parent_id, ChannelFolder) + roots
            roots += 1
        else:
            up = created["/".join(parts[:-1])]
            pid, name = up.id, parts[-1]
            pos = sum(1 for k, f in created.items() if f.parent_id == up.id)
        folder = ChannelFolder(channel_id=ctx.ch.id, parent_id=pid, name=name, position=pos, hidden=False,
                               created_by=user.id, created_at=now)
        _apply_folder_visibility(folder, vis if len(parts) == 1 else visible, clock.now)
        if folder.visibility == "visible":
            folder.visible_from = None
        db.add(folder)
        db.flush()
        created[key] = folder
    audit(db, user, "channel_folder.upload", f"channel:{ctx.ch.id}",
          {"folders": len(created), "visibility": vis["visibility"]}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx, teachers_only=vis["visibility"] != "visible")
    return {"folders": {k: f.id for k, f in created.items()},
            "roots": [_folder_out(f) for k, f in created.items() if "/" not in k]}


@router.patch("/channels/{channel_id}/folders/{folder_id}")
def patch_folder(channel_id: int, folder_id: int, body: FolderPatch, request: Request,
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Umbenennen, verschieben (``parent_id``, ``null`` = oberste Ebene), sortieren, Freigabe (``visibility`` wie beim
    Material inkl. zur Stunde/ab Zeitpunkt; ``hidden`` = alt). Klassenräume: nur eigene Ordner (s. Kopf)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    folder = _get_folder(db, ctx, folder_id)
    assert folder is not None
    ctx.need_edit(folder.created_by)
    fields = body.model_fields_set
    if body.name is not None:
        name = logic.clean_name(body.name, 120)
        if not name:
            raise HTTPException(422, "Bitte einen Ordnernamen angeben")
        folder.name = name
    if "parent_id" in fields and body.parent_id != folder.parent_id:
        folders = _folders(db, ctx.ch.id)
        by_id = {f.id: f for f in folders}
        if body.parent_id is not None:
            parent = _get_folder(db, ctx, body.parent_id)
            assert parent is not None
            if parent.id == folder.id or parent.id in logic.descendant_folder_ids(folders, folder.id):
                raise HTTPException(422, "Ein Ordner kann nicht in sich selbst verschoben werden")
            if _folder_depth(by_id, parent.id) + _subtree_height(folders, folder.id) > MAX_FOLDER_DEPTH:
                raise HTTPException(422, f"Ordner lassen sich höchstens {MAX_FOLDER_DEPTH} Ebenen tief verschachteln")
        folder.parent_id = body.parent_id
        if body.position is None:
            folder.position = _next_position(db, ctx.ch.id, body.parent_id, ChannelFolder)
    if body.position is not None:
        folder.position = body.position
    vis = _folder_fields(ctx, body, clock)
    released = _apply_folder_visibility(folder, vis, clock.now) if vis is not None else False
    folder.updated_at = utcnow()
    if released:
        action = {"hidden": "channel_folder.hide", "visible": "channel_folder.show"}.get(
            folder.effective_visibility, "channel_folder.release")
        audit(db, user, action, f"channel_folder:{folder.id}",
              {"channel_id": ctx.ch.id, "visibility": folder.effective_visibility,
               "lesson_date": folder.lesson_date, "visible_from": iso(folder.visible_from)}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _folder_out(folder)


@router.delete("/channels/{channel_id}/folders/{folder_id}")
def delete_folder(channel_id: int, folder_id: int, request: Request, force: bool = False,
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Ordner in den Papierkorb legen; mit Inhalt (Unterordner/Material inkl. Abgaben) nur mit ``?force=1`` (409 nennt
    die Anzahl).
    Klassenräume: nur wenn Ordner, Unterordner und Material darin eigene sind (außer Klassenleitung/Verwaltung)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    folder = _get_folder(db, ctx, folder_id)
    assert folder is not None
    ctx.need_edit(folder.created_by)
    folders = _folders(db, ctx.ch.id)
    subtree = {folder.id} | logic.descendant_folder_ids(folders, folder.id)
    items = list(db.scalars(select(ChannelItem).where(ChannelItem.channel_id == ctx.ch.id,
                                                      ChannelItem.folder_id.in_(sorted(subtree)))))
    if not ctx.manages_all and (any(not ctx.may_edit(i.created_by) for i in items)
                                or any(not ctx.may_edit(f.created_by) for f in folders if f.id in subtree)):
        raise HTTPException(403, "Der Ordner enthält Material anderer Lehrkräfte – löschen dürfen ihn nur die "
                            "Klassenleitung und die Kursraum-Verwaltung")
    n_sub = 0
    if items:
        n_sub = int(db.scalar(select(func.count()).select_from(AssignmentSubmission).where(
            AssignmentSubmission.item_id.in_([i.id for i in items]))) or 0)
    if (items or len(subtree) > 1) and not force:
        raise HTTPException(409, {"message": f"Der Ordner „{folder.name}“ enthält {len(subtree) - 1} Unterordner, "
                                  f"{len(items)} Materialien und {n_sub} Abgaben. Wirklich löschen?",
                                  "folders": len(subtree) - 1, "items": len(items), "submissions": n_sub})
    _trash_rows(items=items, folders=[f for f in folders if f.id in subtree], user=user)
    audit(db, user, "channel_folder.delete", f"channel_folder:{folder_id}",
          {"channel_id": ctx.ch.id, "folders": len(subtree), "items": len(items), "submissions": n_sub,
           "trash": True}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"deleted": folder_id, "folders": len(subtree), "items": len(items), "trashed": True}


@router.post("/channels/{channel_id}/reorder")
def reorder(channel_id: int, body: ReorderIn, user: AuthUser = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    """Reihenfolge der Ordner und Materialien innerhalb eines Ordners (``parent_id``, ``null`` = oberste Ebene)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    _get_folder(db, ctx, body.parent_id)
    for pos, fid in enumerate(dict.fromkeys(body.folder_ids)):
        f = db.get(ChannelFolder, fid)
        if f is None or f.channel_id != ctx.ch.id or f.parent_id != body.parent_id:
            raise HTTPException(422, f"Ordner {fid} liegt nicht in diesem Ordner")
        if f.position != pos:
            ctx.need_edit(f.created_by)
        f.position = pos
    for pos, iid in enumerate(dict.fromkeys(body.item_ids)):
        it = db.get(ChannelItem, iid)
        if it is None or it.channel_id != ctx.ch.id or it.folder_id != body.parent_id:
            raise HTTPException(422, f"Material {iid} liegt nicht in diesem Ordner")
        if it.position != pos:
            ctx.need_edit(it.created_by)
        it.position = pos
    db.commit()
    _notify(db, ctx)
    return {"ok": True}


# =========================================================================== Material
def _item_title(db: Session, body_type: str, title: str, url: Optional[str], file_id: Optional[str]) -> str:
    title = logic.clean_name(title, 200)
    if title:
        return title
    if body_type == "file" and file_id:
        meta = files.get_file(db, file_id)
        if meta is not None:
            return _stem(meta.filename)
    if body_type == "link" and url:
        from urllib.parse import urlsplit
        return (urlsplit(url).netloc or url)[:200]
    raise HTTPException(422, "Bitte einen Titel angeben")


def _single_item_out(db: Session, ctx: Ctx, item: ChannelItem, clock: Clock, *, body: bool = False) -> dict:
    hidden = clock.folder_states(_folders(db, ctx.ch.id)) if item.folder_id else {}
    has_body = bool(item.body_enc)
    out = _items_out(db, ctx, [(item, has_body)], hidden, clock, None)
    entry = out[0] if out else {"id": item.id}
    if body:
        entry["body"] = item.read_text("body")
    return entry


@router.post("/channels/{channel_id}/items", status_code=201)
def create_item(channel_id: int, body: ItemIn, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Material anlegen: Datei (eigener Upload aus ``POST /files``), Link (nur http/https), Textseite (Markdown,
    verschlüsselt) oder Aufgabe (Beschreibung, Frist, Anhänge) – mit Sichtbarkeit inkl. „zur Stunde“."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    _check_item_capacity(db, ctx.ch.id, 1)
    folder = _get_folder(db, ctx, body.folder_id)
    url = None
    if body.type == "link":
        url = logic.clean_url(body.url or "")
        if url is None:
            raise HTTPException(422, "Bitte eine gültige Adresse mit http:// oder https:// angeben")
    if body.type == "file" and not body.file_id:
        raise HTTPException(422, "Bitte eine Datei hochladen")
    title = _item_title(db, body.type, body.title, url, body.file_id)
    if body.info_card and (ctx.ch.kind != logic.CLASS or body.type != "text" or folder is not None):
        raise HTTPException(422, "Infokarten gibt es nur als Textseite im Klassenraum (ohne Ordner)")
    if body.info_card:
        body = body.model_copy(update={"visibility": "visible", "visible_from": None, "lesson": None,
                                       "lesson_material": False, "submittable": False})
    vis = _visibility_fields(ctx, body.visibility, body.visible_from, body.lesson, clock)
    due_at = _to_utc(body.due_at, "die Abgabefrist") if body.type == "assignment" else None
    item = ChannelItem(channel_id=ctx.ch.id, folder_id=folder.id if folder else None, type=body.type, title=title,
                       body_enc="", url=url, allow_late=body.allow_late, due_at=due_at,
                       position=_next_position(db, ctx.ch.id, folder.id if folder else None),
                       created_by=user.id, created_at=utcnow(), info_card=body.info_card)
    _apply_visibility(item, vis, clock.now)
    if item.visibility == "visible":
        item.visible_from = None
    _apply_material_flags(item, body.lesson_material, body.material_date, body.submittable, clock)
    db.add(item)
    db.flush()
    text = logic.clean_text(body.body, MAX_BODY) if body.type in ("text", "assignment") else ""
    if body.type == "text" and not text and not body.attachment_ids:
        raise HTTPException(422, "Die Textseite ist leer")
    item.write_text("body", text)
    if body.type == "file":
        files.attach(db, body.file_id or "", user, REF_ITEM, item.id)
        item.file_id = body.file_id
    if body.attachment_ids and body.type != "link":
        ids = list(dict.fromkeys(body.attachment_ids))
        files.attach_many(db, ids, user, REF_ITEM, item.id, max_files=MAX_ATTACHMENTS)
        item.attachment_ids = ids
    audit(db, user, "channel_item.create", f"channel_item:{item.id}",
          {"channel_id": ctx.ch.id, "type": item.type, "visibility": item.visibility}, ip=client_ip(request))
    db.commit()
    out = _single_item_out(db, ctx, item, clock)
    _notify(db, ctx, teachers_only=not out.get("visible"))
    if out.get("visible"):  # Glocke: Schüler/innen und Eltern (notification_hooks)
        from schulmanager.server import notification_hooks
        notification_hooks.channel_item_created(db, ctx, [item])
    return out


@router.post("/channels/{channel_id}/items/files", status_code=201)
def create_file_items(channel_id: int, body: FilesIn, request: Request, user: AuthUser = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    """Mehrfach-Upload: hochgeladene Dateien (``POST /files?purpose=channel_material``) als Material in einen Ordner."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    ids = list(dict.fromkeys(body.file_ids))
    _check_item_capacity(db, ctx.ch.id, len(ids))
    folder = _get_folder(db, ctx, body.folder_id)
    vis = _visibility_fields(ctx, body.visibility, body.visible_from, body.lesson, clock)
    pos = _next_position(db, ctx.ch.id, folder.id if folder else None)
    created: list[ChannelItem] = []
    for n, file_id in enumerate(ids):
        meta = files.get_file(db, file_id)
        if meta is None or meta.owner_user_id != user.id:
            raise files.FileError(404, "not_found", "Datei nicht gefunden")
        item = ChannelItem(channel_id=ctx.ch.id, folder_id=folder.id if folder else None, type="file",
                           title=_stem(meta.filename), body_enc="", position=pos + n, created_by=user.id,
                           created_at=utcnow())
        _apply_visibility(item, vis, clock.now)
        if item.visibility == "visible":
            item.visible_from = None
        _apply_material_flags(item, body.lesson_material, body.material_date, body.submittable, clock)
        db.add(item)
        db.flush()
        files.attach(db, file_id, user, REF_ITEM, item.id)
        item.file_id = file_id
        created.append(item)
    audit(db, user, "channel_item.upload", f"channel:{ctx.ch.id}",
          {"items": [i.id for i in created], "visibility": vis["visibility"]}, ip=client_ip(request))
    db.commit()
    hidden = clock.folder_states(_folders(db, ctx.ch.id))
    out = _items_out(db, ctx, [(i, False) for i in created], hidden, clock, None)
    _notify(db, ctx, teachers_only=not any(e.get("visible") for e in out))
    shown = {e.get("id") for e in out if e.get("visible")}
    if shown:  # Glocke: Schüler/innen und Eltern (notification_hooks)
        from schulmanager.server import notification_hooks
        notification_hooks.channel_item_created(db, ctx, [i for i in created if i.id in shown])
    return {"items": out}


@router.get("/channels/{channel_id}/items/{item_id}")
def get_item(channel_id: int, item_id: int, student_id: Optional[str] = Query(None, max_length=40),
             user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Material mit Text (Markdown) – Teilnehmende/Eltern nur, wenn freigegeben (sonst 404)."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    item, _ = _visible_item_or_404(db, ctx, item_id, clock)
    out = _single_item_out(db, ctx, item, clock, body=True)
    if takes_submissions(item) and ctx.pupil:
        sub = db.scalar(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id,
                                                           AssignmentSubmission.student_user_id == ctx.pupil_uid)
                        ) if ctx.pupil_uid else None
        from . import features_assignments as fa

        out["my_submission"] = fa._submission_out(db, ctx, item, sub, clock,
                                                  settings=at.settings_for(db, item.id)) if sub else None
    return out


@router.patch("/channels/{channel_id}/items/{item_id}")
def patch_item(channel_id: int, item_id: int, body: ItemPatch, request: Request,
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Material ändern: Titel, Text, Link, Datei ersetzen, Anhänge, Ordner/Position, Sichtbarkeit, Frist
    (Klassenräume: nur eigenes, außer Klassenleitung/Kursraum-Verwaltung)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    item = _get_item(db, ctx, item_id)
    ctx.need_edit(item.created_by)
    fields = body.model_fields_set
    if item.info_card and (body.folder_id is not None or body.lesson is not None or body.due_at is not None
                           or body.visibility not in (None, "visible") or body.lesson_material or body.submittable):
        raise HTTPException(422, "Infokarten sind immer sichtbar und liegen in keinem Ordner")
    changed: list[str] = []
    if body.title is not None:
        title = logic.clean_name(body.title, 200)
        if not title:
            raise HTTPException(422, "Bitte einen Titel angeben")
        if title != item.title:
            item.title = title
            changed.append("title")
    if body.body is not None and item.type in ("text", "assignment"):
        item.write_text("body", logic.clean_text(body.body, MAX_BODY))
        changed.append("body")
    if body.url is not None and item.type == "link":
        url = logic.clean_url(body.url)
        if url is None:
            raise HTTPException(422, "Bitte eine gültige Adresse mit http:// oder https:// angeben")
        if url != item.url:
            item.url = url
            changed.append("url")
    if body.file_id is not None and item.type == "file" and body.file_id != item.file_id:
        files.attach(db, body.file_id, user, REF_ITEM, item.id)
        if item.file_id:
            files.delete(db, item.file_id, user, hard=True)
        item.file_id = body.file_id
        changed.append("file")
    if body.attachment_ids is not None and item.type != "link":
        new_ids = list(dict.fromkeys(body.attachment_ids))
        old_ids = list(item.attachment_ids or [])
        added = [i for i in new_ids if i not in old_ids]
        removed = [i for i in old_ids if i not in new_ids]
        if added:
            files.attach_many(db, added, user, REF_ITEM, item.id, max_files=MAX_ATTACHMENTS)
        for fid in removed:
            files.delete(db, fid, user, hard=True)
        if added or removed or new_ids != old_ids:
            item.attachment_ids = new_ids
            changed.append("attachments")
    if "folder_id" in fields and body.folder_id != item.folder_id:
        folder = _get_folder(db, ctx, body.folder_id)
        item.folder_id = folder.id if folder else None
        if body.position is None:
            item.position = _next_position(db, ctx.ch.id, item.folder_id)
        changed.append("folder")
    if body.position is not None:
        item.position = body.position
    released = False
    if body.visibility is not None:
        vis = _visibility_fields(ctx, body.visibility, body.visible_from, body.lesson, clock)
        released = _apply_visibility(item, vis, clock.now)
    if body.lesson_material is not None or body.submittable is not None or "material_date" in fields:
        before = (item.lesson_material, item.material_date, item.submittable)
        _apply_material_flags(item, item.lesson_material if body.lesson_material is None else body.lesson_material,
                              body.material_date if "material_date" in fields else
                              (date.fromisoformat(item.material_date) if item.material_date else None),
                              item.submittable if body.submittable is None else body.submittable, clock)
        if before != (item.lesson_material, item.material_date, item.submittable):
            changed.append("material")
    if item.type == "assignment":
        if "due_at" in fields:
            due = _to_utc(body.due_at, "die Abgabefrist")
            if due != item.due_at:
                item.due_at = due
                changed.append("due_at")
        if body.allow_late is not None and body.allow_late != item.allow_late:
            item.allow_late = body.allow_late
            changed.append("allow_late")
    if changed or released or body.position is not None:
        item.updated_at = utcnow()
        if released:
            audit(db, user, "channel_item.release", f"channel_item:{item.id}",
                  {"channel_id": ctx.ch.id, "visibility": item.visibility, "lesson_date": item.lesson_date,
                   "lesson_period": item.lesson_period, "visible_from": iso(item.visible_from)},
                  ip=client_ip(request))
        if changed:
            audit(db, user, "channel_item.update", f"channel_item:{item.id}",
                  {"channel_id": ctx.ch.id, "fields": changed}, ip=client_ip(request))
        db.commit()
        _notify(db, ctx)
    return _single_item_out(db, ctx, item, clock, body=True)


@router.post("/channels/{channel_id}/items/visibility")
def set_visibility(channel_id: int, body: VisibilityIn, request: Request, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Sichtbarkeit mehrerer Materialien und/oder ganzer Ordner auf einmal setzen (sofort, verborgen, ab Zeitpunkt,
    zur Stunde, ``next_lesson`` = zur nächsten Stunde)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    if not body.item_ids and not body.folder_ids:
        raise HTTPException(422, "Bitte Material oder Ordner auswählen")
    vis = _visibility_fields(ctx, body.visibility, body.visible_from, body.lesson, clock)
    items = [_get_item(db, ctx, iid) for iid in dict.fromkeys(body.item_ids)]
    folders_sel = [_get_folder(db, ctx, fid) for fid in dict.fromkeys(body.folder_ids)]
    for obj in [*items, *folders_sel]:
        ctx.need_edit(obj.created_by if obj is not None else None)
    changed = [item.id for item in items if _apply_visibility(item, dict(vis), clock.now)]
    changed_folders = [f.id for f in folders_sel if f is not None and _apply_folder_visibility(f, vis, clock.now)]
    now = utcnow()
    for item in items:
        if item.id in changed:
            item.updated_at = now
    for f in folders_sel:
        if f is not None and f.id in changed_folders:
            f.updated_at = now
    if changed or changed_folders:
        audit(db, user, "channel_item.release", f"channel:{ctx.ch.id}",
              {"items": changed, "folders": changed_folders, "visibility": vis["visibility"],
               "lesson_date": vis.get("lesson_date"), "lesson_period": vis.get("lesson_period"),
               "visible_from": iso(vis.get("visible_from"))}, ip=client_ip(request))
        db.commit()
        _notify(db, ctx)
    all_folders = _folders(db, ctx.ch.id)
    hidden = clock.folder_states(all_folders)
    return {"items": _items_out(db, ctx, [(i, bool(i.body_enc)) for i in items], hidden, clock, None),
            "folders": [f for f in _folders_out(ctx, all_folders, hidden, clock) if f["id"] in body.folder_ids],
            "changed": changed, "changed_folders": changed_folders,
            "lesson": {"date": vis["lesson_date"], "period": vis["lesson_period"], "lesson_id": vis["lesson_id"]}
            if vis.get("lesson_date") else None}


@router.delete("/channels/{channel_id}/items/{item_id}")
def delete_item(channel_id: int, item_id: int, request: Request, force: bool = False,
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Material in den Papierkorb legen (30 Tage wiederherstellbar, ``trash_retention_days``); Aufgaben mit Abgaben
    nur mit ``?force=1`` (Klassenräume: nur eigenes, außer Klassenleitung/Kursraum-Verwaltung)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    item = _get_item(db, ctx, item_id)
    ctx.need_edit(item.created_by)
    n_sub = int(db.scalar(select(func.count()).select_from(AssignmentSubmission).where(
        AssignmentSubmission.item_id == item.id)) or 0)
    if n_sub and not force:
        raise HTTPException(409, {"message": f"Zu dieser Aufgabe gibt es {n_sub} Abgaben. Wirklich mit allen "
                                  "Abgaben löschen?", "submissions": n_sub})
    audit(db, user, "channel_item.delete", f"channel_item:{item.id}",
          {"channel_id": ctx.ch.id, "type": item.type, "submissions": n_sub, "trash": True}, ip=client_ip(request))
    _trash_rows(items=[item], folders=[], user=user)
    db.commit()
    _notify(db, ctx)
    return {"deleted": item_id, "trashed": True}


# =========================================================================== Kopieren (Parallelkurse)
def _copy_item(db: Session, user: AuthUser, src: ChannelItem, target: Channel, folder_id: Optional[int],
               position: int, keep_visibility: bool, now: datetime) -> ChannelItem:
    item = ChannelItem(channel_id=target.id, folder_id=folder_id, type=src.type, title=src.title, body_enc="",
                       url=src.url, due_at=src.due_at, allow_late=src.allow_late, position=position,
                       created_by=user.id, created_at=now)
    if keep_visibility and src.visibility in ("visible", "hidden", "scheduled"):
        item.visibility = src.visibility
        item.visible_from = src.visible_from if src.visibility == "scheduled" else None
    else:  # an Stunden gebundenes Material gehört zu den Stunden des Quellkurses → im Ziel erst verborgen
        item.visibility = "hidden"
    db.add(item)
    db.flush()
    item.write_text("body", src.read_text("body") if src.body_enc else "")
    if src.file_id:
        copy = files.duplicate(db, src.file_id, user, PURPOSE_MATERIAL)
        files.attach(db, copy.id, user, REF_ITEM, item.id)
        item.file_id = copy.id
    attachments = []
    for fid in src.attachment_ids or []:
        if files.get_file(db, fid) is None:
            continue
        copy = files.duplicate(db, fid, user, PURPOSE_MATERIAL)
        files.attach(db, copy.id, user, REF_ITEM, item.id)
        attachments.append(copy.id)
    item.attachment_ids = attachments or None
    src_settings = at.settings_for(db, src.id)
    if src_settings is not None and src_settings.rubric():       # Raster/Punkte/Notenschlüssel mitkopieren (keine Gruppen)
        dst = at.get_or_create_settings(db, item.id)
        dst.set_rubric(src_settings.rubric())
        dst.rubric_title = src_settings.rubric_title
        dst.max_points = src_settings.max_points
        dst.grade_scale = src_settings.grade_scale
    elif src_settings is not None and (src_settings.max_points or src_settings.grade_scale):
        dst = at.get_or_create_settings(db, item.id)
        dst.max_points = src_settings.max_points
        dst.grade_scale = src_settings.grade_scale
    return item


@router.post("/channels/{channel_id}/copy")
def copy_material(channel_id: int, body: CopyIn, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    """Material und Ordner in einen anderen eigenen Kursraum kopieren (z. B. Parallelkurs); Dateien werden
    dupliziert, Abgaben nicht. Im Ziel standardmäßig verborgen (an Stunden gebundenes Material immer)."""
    src = _ctx(db, user, channel_id)
    if not src.teacher:
        raise HTTPException(403, "Nur Lehrende dieses Kursraums können Material kopieren")
    dst = _ctx(db, user, body.target_channel_id, manage=True)
    target_folder = _get_folder(db, dst, body.target_folder_id)
    src_folders = _folders(db, src.ch.id)
    by_id = {f.id: f for f in src_folders}
    roots = []
    for fid in dict.fromkeys(body.folder_ids):
        f = by_id.get(fid)
        if f is None:
            raise HTTPException(404, f"Ordner {fid} nicht gefunden")
        roots.append(f)
    items = []
    for iid in dict.fromkeys(body.item_ids):
        it = db.get(ChannelItem, iid)
        if it is None or it.channel_id != src.ch.id:
            raise HTTPException(404, f"Material {iid} nicht gefunden")
        items.append(it)
    if not roots and not items:
        raise HTTPException(422, "Bitte Material oder Ordner auswählen")
    subtree_ids: set[int] = set()
    for f in roots:
        subtree_ids |= {f.id} | logic.descendant_folder_ids(src_folders, f.id)
    folder_items = list(db.scalars(select(ChannelItem).where(ChannelItem.channel_id == src.ch.id,
                                                             ChannelItem.folder_id.in_(sorted(subtree_ids)))
                                   .order_by(ChannelItem.position, ChannelItem.id))) if subtree_ids else []
    loose = [it for it in items if it.folder_id not in subtree_ids]
    total = len(folder_items) + len(loose)
    if total > MAX_COPY:
        raise HTTPException(422, f"Höchstens {MAX_COPY} Materialien je Kopiervorgang")
    _check_item_capacity(db, dst.ch.id, total)
    dst_folders = _folders(db, dst.ch.id)
    if len(dst_folders) + len(subtree_ids) > MAX_FOLDERS:
        raise HTTPException(409, f"Höchstens {MAX_FOLDERS} Ordner je Kursraum")
    base_depth = _folder_depth({f.id: f for f in dst_folders}, target_folder.id if target_folder else None)
    for f in roots:
        if base_depth + _subtree_height(src_folders, f.id) > MAX_FOLDER_DEPTH:
            raise HTTPException(422, f"Ordner lassen sich höchstens {MAX_FOLDER_DEPTH} Ebenen tief verschachteln")
    now = utcnow()
    mapping: dict[int, int] = {}
    target_parent = target_folder.id if target_folder else None
    copied_folders = 0

    def copy_folder(f: ChannelFolder, parent_id: Optional[int], position: int) -> None:
        nonlocal copied_folders
        # Freigabe wie beim Material: geplante Ordner bleiben geplant (nur mit keep_visibility), an Stunden des
        # Quellkurses gebundene werden verborgen – nie sofort sichtbar, was in der Quelle noch nicht frei ist
        vis = f.effective_visibility
        if vis == "lesson" or (vis == "scheduled" and not body.keep_visibility):
            vis = "hidden"
        new = ChannelFolder(channel_id=dst.ch.id, parent_id=parent_id, name=f.name, position=position,
                            hidden=vis == "hidden", visibility=vis,
                            visible_from=f.visible_from if vis == "scheduled" else None,
                            created_by=user.id, created_at=now)
        db.add(new)
        db.flush()
        mapping[f.id] = new.id
        copied_folders += 1
        for child in sorted((c for c in src_folders if c.parent_id == f.id), key=lambda c: (c.position, c.id)):
            copy_folder(child, new.id, child.position)

    pos = _next_position(db, dst.ch.id, target_parent, ChannelFolder)
    top_roots = [f for f in roots if not any(a in subtree_ids for a in logic.folder_path_ids(src_folders, f.parent_id))]
    for n, f in enumerate(top_roots):
        copy_folder(f, target_parent, pos + n)
    created = 0
    for it in folder_items:
        _copy_item(db, user, it, dst.ch, mapping.get(it.folder_id or -1), it.position, body.keep_visibility, now)
        created += 1
    pos = _next_position(db, dst.ch.id, target_parent)
    for n, it in enumerate(loose):
        _copy_item(db, user, it, dst.ch, target_parent, pos + n, body.keep_visibility, now)
        created += 1
    audit(db, user, "channel.copy", f"channel:{dst.ch.id}",
          {"from_channel_id": src.ch.id, "items": created, "folders": copied_folders,
           "keep_visibility": body.keep_visibility}, ip=client_ip(request))
    db.commit()
    _notify(db, dst, teachers_only=not body.keep_visibility)
    return {"target_channel_id": dst.ch.id, "items": created, "folders": copied_folders}


# =========================================================================== ZIP-Download
class _ZipSink(io.RawIOBase):
    """Nicht spulbarer Puffer: ``zipfile`` schreibt im Streaming-Modus, der Generator leert ihn laufend
    (Klartext landet so nie auf der Platte)."""

    def __init__(self) -> None:
        super().__init__()
        self.buffer = bytearray()

    def writable(self) -> bool:
        return True

    def write(self, data) -> int:  # type: ignore[override]
        self.buffer += data
        return len(data)

    def drain(self) -> bytes:
        out = bytes(self.buffer)
        self.buffer.clear()
        return out


def _zip_stream(entries: list[tuple[str, Any]]) -> Iterator[bytes]:
    """``entries`` = ``(pfad, bytes | StoredFile)``; Dateien werden blockweise entschlüsselt."""
    sink = _ZipSink()
    with zipfile.ZipFile(sink, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, payload in entries:
            info = zipfile.ZipInfo(path, date_time=datetime.now().timetuple()[:6])
            if isinstance(payload, bytes):
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, payload)
            else:
                info.compress_type = zipfile.ZIP_STORED if payload.kind in _STORED_KINDS else zipfile.ZIP_DEFLATED
                with zf.open(info, "w") as out:
                    for block in files.iter_plaintext(payload):
                        out.write(block)
                        if len(sink.buffer) >= 1024 * 1024:
                            yield sink.drain()
            if sink.buffer:
                yield sink.drain()
    yield sink.drain()


@router.get("/channels/{channel_id}/zip")
def download_zip(channel_id: int, request: Request, folder_id: Optional[int] = None,
                 students_view: bool = Query(False, description="Lehrende: nur für Teilnehmende Sichtbares"),
                 student_id: Optional[str] = Query(None, max_length=40, description="Eltern: Kind"),
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> StreamingResponse:
    """Ordner (oder ganzer Kursraum) als ZIP – nur Inhalte, die das Konto sehen darf: Dateien, Anhänge, Textseiten
    und Aufgaben als Markdown, Links gesammelt in „Links.txt“."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    folders = _folders(db, ctx.ch.id)
    hidden = clock.folder_states(folders)
    only_visible = ctx.pupil or students_view
    root = _get_folder(db, ctx, folder_id)
    if root is not None and only_visible and not hidden[root.id].visible:
        raise HTTPException(404, "Ordner nicht gefunden")
    by_id = {f.id: f for f in folders}
    scope = ({root.id} | logic.descendant_folder_ids(folders, root.id)) if root else None
    base = len(logic.folder_path_ids(folders, root.id)) if root else 0

    def folder_path(fid: Optional[int]) -> str:
        if fid is None:
            return ""
        ids = logic.folder_path_ids(folders, fid)[base:]
        return "".join(logic.zip_safe_name(by_id[i].name, "Ordner") + "/" for i in ids)

    entries: list[tuple[str, Any]] = []
    links: dict[str, list[str]] = defaultdict(list)
    taken: dict[str, set[str]] = defaultdict(set)
    total = 0
    rows = [r for r in _load_items(db, [ctx.ch.id]) if scope is None or r[0].folder_id in scope]
    rows.sort(key=lambda r: (logic.folder_path_ids(folders, r[0].folder_id), r[0].position, r[0].id))
    for item, _ in rows:
        if only_visible and not clock.visibility(item, hidden).visible:
            continue
        prefix = folder_path(item.folder_id)
        if item.type == "link":
            links[prefix].append(f"{item.title}: {item.url}")
            continue
        if item.type in ("text", "assignment"):
            text = item.read_text("body")
            head = f"# {item.title}\n\n"
            if item.type == "assignment" and item.due_at:
                head += f"Abgabe bis: {logic.utc_to_local(item.due_at).strftime('%d.%m.%Y %H:%M')}\n\n"
            suffix = " (Aufgabe)" if item.type == "assignment" else ""
            name = logic.unique_name(logic.zip_safe_name(item.title + suffix, "Text") + ".md", taken[prefix])
            entries.append((prefix + name, (head + text + "\n").encode("utf-8")))
        for fid in [item.file_id, *(item.attachment_ids or [])]:
            meta = files.get_file(db, fid) if fid else None
            if meta is None:
                continue
            total += meta.size
            if total > ZIP_MAX_BYTES:
                raise HTTPException(413, f"Zu groß für einen ZIP-Download (über {ZIP_MAX_BYTES // 1024 // 1024} MB) "
                                    "– bitte einzelne Ordner herunterladen")
            name = logic.unique_name(logic.zip_safe_name(meta.filename, "Datei"), taken[prefix])
            _ = meta.filename  # Dateiname vor dem Streamen entschlüsseln (keine DB-Zugriffe im Generator)
            entries.append((prefix + name, meta))
        if len(entries) > ZIP_MAX_FILES:
            raise HTTPException(413, f"Zu viele Dateien für einen ZIP-Download (über {ZIP_MAX_FILES})")
    for prefix, lines in links.items():
        name = logic.unique_name("Links.txt", taken[prefix])
        entries.append((prefix + name, ("\r\n".join(lines) + "\r\n").encode("utf-8")))
    if not entries:
        raise HTTPException(404, "In diesem Ordner gibt es nichts herunterzuladen")
    audit(db, user, "channel.zip_download", f"channel:{ctx.ch.id}",
          {"folder_id": folder_id, "files": len(entries), "bytes": total}, ip=client_ip(request))
    db.commit()
    title = root.name if root else (ctx.spec.title if ctx.spec else ctx.ch.title)
    headers = {"Content-Disposition": files.content_disposition(logic.zip_safe_name(title, "Kursraum") + ".zip"),
               "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store",
               "Referrer-Policy": "no-referrer"}
    return StreamingResponse(_zip_stream(entries), media_type="application/zip", headers=headers)


# =========================================================================== Kommende Stunden
@router.get("/channels/{channel_id}/lessons")
def upcoming(channel_id: int, start: Optional[str] = Query(None, alias="from"),
             days: int = Query(logic.DEFAULT_UPCOMING_DAYS, ge=1, le=logic.MAX_UPCOMING_DAYS),
             all: bool = Query(False, description="Klassenkursraum: alle Stunden der Klasse"),  # noqa: A002
             user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Kommende Unterrichtsstunden des Kursraums (Standard: 4 Wochen ab heute) aus dem Stundenplan inkl. laufender Woche;
    Ferien/Feiertage als ``skipped``, Entfall/Verlegung/Vertretung/Raumänderung/Klausur aus dem Vertretungsplan
    markiert; je Stunde das bereits gebundene Material."""
    ctx = _ctx(db, user, channel_id)
    if not ctx.staff_view:
        raise HTTPException(403, "Nur für Lehrende")
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    d0 = parse_date(start, clock.today, name="from")
    if ctx.ch.kind == logic.CUSTOM or ctx.spec is None:
        return {"from": d0.isoformat(), "to": d0.isoformat(), "lessons": [], "skipped": [], "custom": True,
                "all": False}
    teacher_filter = user.teacher_id if (ctx.ch.kind == logic.CLASS and ctx.teacher and not all) else None
    res = logic.upcoming_lessons(ctx.school, ctx.ch.kind, ctx.ch.ref or "", d0, days, plan_for=clock.plan,
                                 teacher_id=teacher_filter, now=clock.now)
    shows_all = teacher_filter is None
    if teacher_filter and not res["lessons"]:
        res = logic.upcoming_lessons(ctx.school, ctx.ch.kind, ctx.ch.ref or "", d0, days, plan_for=clock.plan,
                                     now=clock.now)
        shows_all = True
    bound: dict[str, list[dict]] = defaultdict(list)
    for item_id, title, itype, ldate, lid, lper in db.execute(
            select(ChannelItem.id, ChannelItem.title, ChannelItem.type, ChannelItem.lesson_date,
                   ChannelItem.lesson_id, ChannelItem.lesson_period)
            .where(ChannelItem.channel_id == ctx.ch.id, ChannelItem.visibility == "lesson",
                   ChannelItem.lesson_date >= res["from"], ChannelItem.lesson_date <= res["to"])
            .order_by(ChannelItem.position, ChannelItem.id)):
        bound[logic.lesson_key(ldate, lid or "", lper or 0)].append({"id": item_id, "title": title, "type": itype})
    lessons = [{**_lesson_json(lesson), "items": bound.get(lesson["key"], [])} for lesson in res["lessons"]]
    return {"from": res["from"], "to": res["to"], "lessons": lessons, "skipped": res["skipped"], "custom": False,
            "all": shows_all, "now": iso(clock.now)}


def _viewer_student(ctx: Ctx, student_id: Optional[str]) -> Optional[str]:
    """Schüler/in, deren Anwesenheit gezeigt wird: eigene (Schüler/in) bzw. ein Kind im Kursraum (Eltern)."""
    if ctx.student:
        return getattr(ctx.user, "student_id", None)
    if ctx.parent:
        kids = [s for s in (getattr(ctx.user, "student_ids", None) or [])]
        if ctx.spec is not None:
            members = set(logic.channel_student_ids(ctx.school, ctx.spec.kind, ctx.spec.ref))
            kids = [s for s in kids if s in members] or kids
        if student_id and student_id in kids:
            return student_id
        return kids[0] if kids else None
    return None


# Meldungen, die „nicht da“ bedeuten (zu spät / früher gegangen zählt nicht – das bleibt im Klassenbuch)
ABSENT_KINDS = ("krank", "fehlt", "beurlaubung")


def _lesson_attendance(db: Session, sid: str, d0: date, end: date, reg: dict) -> tuple[dict, dict]:
    """Je (Datum, Stunde) der Status der Schülerin/des Schülers aus Klassenbuch und Krankmeldungen."""
    from schulmanager.server.db_models import StudentAbsence

    from .features_register import _entry_out
    marks: dict[tuple[str, int], str] = {}
    for (d, _lid, period), row in reg.items():
        st = ((_entry_out(row) or {}).get("attendance") or {}).get(sid)
        if st:
            marks[(d, period)] = {"present": "present", "late": "partial", "left": "partial"}.get(st.get("status"),
                                                                                                 "absent")
    reported: dict[str, list] = defaultdict(list)
    for a in db.scalars(select(StudentAbsence).where(StudentAbsence.student_id == sid,
                                                     StudentAbsence.date_to >= d0.isoformat(),
                                                     StudentAbsence.date_from <= end.isoformat())):
        reported[a.date_from].append(a)
        if a.date_to != a.date_from:
            day = date.fromisoformat(a.date_from)
            while day < date.fromisoformat(a.date_to):
                day += timedelta(days=1)
                reported[day.isoformat()].append(a)
    return marks, reported


@router.post("/channels/{channel_id}/items/{item_id}/viewed")
def mark_viewed(channel_id: int, item_id: int, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Material geöffnet (für den Hinweis „noch nicht angesehen“ im Bereich Unterricht)."""
    ctx = _ctx(db, user, channel_id)
    item = db.get(ChannelItem, item_id)
    if item is None or item.channel_id != ctx.ch.id:
        raise HTTPException(404, "Inhalt nicht gefunden")
    if ctx.student:
        _visible_item_or_404(db, ctx, item_id, Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx))     # gesperrt/verborgen: kein „gesehen“
    if user.id and db.scalar(select(ChannelItemView.id).where(ChannelItemView.item_id == item_id,
                                                              ChannelItemView.user_id == user.id)) is None:
        db.add(ChannelItemView(item_id=item_id, user_id=user.id, viewed_at=utcnow()))
        db.commit()
    return {"ok": True}


@router.get("/channels/{channel_id}/unterricht")
def lesson_log(channel_id: int, start: Optional[str] = Query(None, alias="from"),
               days: int = Query(28, ge=1, le=120), student_id: Optional[str] = Query(None, max_length=40),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Was im Unterricht gemacht wurde (für alle Teilnehmenden, z. B. nach Krankheit): je stattgefundener Stunde
    (Entfall nicht; Verlegungen am tatsächlichen Tag) das als Unterrichtsmaterial markierte Material dieses Tages
    (nur Freigegebenes) und die an dem Tag gestellten Aufgaben (``assignments``, Link zur Hausaufgabe).
    Klassenbuch-Inhalte (Thema, Hausaufgabe als Text) sind Schulinterna: nur Lehrende und Schulleitung
    (``register: true``) – Schüler/innen, Eltern, Schulbegleitung u. a. nicht. Schüler/innen bzw. Eltern sehen je
    Stunde nur, ob sie gefehlt haben (``attendance: "absent"``, Label krank/beurlaubt/gefehlt; anwesend = nichts),
    und welches Material noch nicht geöffnet wurde (``viewed``). Standard: die letzten 4 Wochen, neueste zuerst."""
    ctx = _ctx(db, user, channel_id)
    clock = Clock(ctx.snap).restrict(db, ctx)
    d1 = clock.today
    d0 = parse_date(start, d1 - timedelta(days=days - 1), name="from")
    end = min(d1, d0 + timedelta(days=days - 1))
    lessons: list[dict[str, Any]] = []
    if ctx.ch.kind != logic.CUSTOM and ctx.spec is not None:
        res = logic.upcoming_lessons(ctx.school, ctx.ch.kind, ctx.ch.ref or "", d0, (end - d0).days + 1,
                                     plan_for=clock.plan, now=clock.now)
        lessons = [x for x in res["lessons"] if x["date"] <= end.isoformat() and x.get("status") != "entfall"
                   and (x["date"] < clock.today.isoformat() or x.get("started"))]
    # Klassenbuch: Thema/Hausaufgabe je Stunde (Anwesenheit bleibt im Klassenbuch)
    from schulmanager.server.feature_models.register import RegisterLesson
    reg: dict[tuple[str, str, int], RegisterLesson] = {}
    lesson_ids = {x["lesson_id"] for x in lessons}
    if lesson_ids:
        for row in db.scalars(select(RegisterLesson).where(RegisterLesson.date >= d0.isoformat(),
                                                           RegisterLesson.date <= end.isoformat(),
                                                           RegisterLesson.lesson_id.in_(lesson_ids))):
            reg.setdefault((row.date, row.lesson_id, row.period), row)
    rows = list(db.execute(select(ChannelItem, (func.length(ChannelItem.body_enc) > 0).label("has_body"))
                           .options(defer(ChannelItem.body_enc))
                           .where(ChannelItem.channel_id == ctx.ch.id, ChannelItem.lesson_material.is_(True),
                                  ChannelItem.material_date >= d0.isoformat(),
                                  ChannelItem.material_date <= end.isoformat())
                           .order_by(ChannelItem.position, ChannelItem.id)).all())
    states = clock.folder_states(_folders(db, ctx.ch.id))
    items = _items_out(db, ctx, [(r[0], bool(r[1])) for r in rows], states, clock, None)
    viewed: set[int] = set()
    if items and user.id:
        viewed = set(db.scalars(select(ChannelItemView.item_id).where(
            ChannelItemView.user_id == user.id, ChannelItemView.item_id.in_([it["id"] for it in items]))))
    for it in items:
        it["viewed"] = it["id"] in viewed
    by_date: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        by_date[it["material_date"]].append(it)
    # Aufgaben (Hausaufgaben), die an diesem Tag gestellt wurden → Link bei der Stunde
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Europe/Berlin")
    a_start = datetime.combine(d0, datetime.min.time(), tz).astimezone(timezone.utc).replace(tzinfo=None)
    a_end = datetime.combine(end + timedelta(days=1), datetime.min.time(), tz).astimezone(timezone.utc).replace(
        tzinfo=None)
    a_rows = list(db.execute(select(ChannelItem, (func.length(ChannelItem.body_enc) > 0).label("has_body"))
                             .options(defer(ChannelItem.body_enc))
                             .where(ChannelItem.channel_id == ctx.ch.id, ChannelItem.type == "assignment",
                                    ChannelItem.created_at >= a_start, ChannelItem.created_at < a_end)
                             .order_by(ChannelItem.position, ChannelItem.id)).all())
    a_day = {r[0].id: r[0].created_at.replace(tzinfo=timezone.utc).astimezone(tz).date().isoformat()
             for r in a_rows}
    assignments_by_date: dict[str, list[dict]] = defaultdict(list)
    for it in _items_out(db, ctx, [(r[0], bool(r[1])) for r in a_rows], states, clock, None):
        assignments_by_date[a_day[it["id"]]].append(it)
    show_register = ctx.staff_view
    sid = _viewer_student(ctx, student_id)
    marks, reported = _lesson_attendance(db, sid, d0, end, reg) if sid else ({}, {})

    def _text(row: Optional[RegisterLesson], field: str) -> str:
        if row is None:
            return ""
        try:
            return crypto.decrypt_text(getattr(row, f"{field}_enc"), row.aad(field)) if getattr(row, f"{field}_enc") \
                else ""
        except Exception:  # noqa: BLE001
            return ""

    out_lessons = []
    used: set[str] = set()
    used_a: set[str] = set()
    for x in sorted(lessons, key=lambda le: (le["date"], le["period"]), reverse=True):
        periods = range(x["period"], x["period"] + max(1, int(x.get("length") or 1)))
        topic = homework = ""
        if show_register:
            rows_reg = [reg[(x["date"], x["lesson_id"], p)] for p in periods if (x["date"], x["lesson_id"], p) in reg]
            topic = " · ".join(dict.fromkeys(t for t in (_text(r, "topic") for r in rows_reg) if t))
            homework = " · ".join(dict.fromkeys(t for t in (_text(r, "homework") for r in rows_reg) if t))
        mats = [] if x["date"] in used else by_date.get(x["date"], [])
        used.add(x["date"])
        subj = x.get("subject")
        tasks = [a for a in assignments_by_date.get(x["date"], [])
                 if f"{x['date']}#{a['id']}" not in used_a and (not a.get("subject") or a.get("subject") == subj)]
        used_a.update(f"{x['date']}#{a['id']}" for a in tasks)
        attendance, att_label = None, ""
        if sid:
            kinds: set[str] = set()
            missed = False
            for p in periods:
                cover = [a for a in reported.get(x["date"], []) if a.kind in ABSENT_KINDS
                         and (not a.periods or p in a.periods)]
                if marks.get((x["date"], p)) == "absent" or cover:
                    missed = True
                    kinds.update(a.kind for a in cover)
            if missed:
                attendance = "absent"
                att_label = "krank" if "krank" in kinds else "beurlaubt" if "beurlaubung" in kinds else "gefehlt"
        out_lessons.append({"date": x["date"], "period": x["period"], "length": x.get("length", 1),
                            "period_label": x.get("period_label"), "time": x.get("time"),
                            "subject": subj, "subject_name": x.get("subject_name"),
                            "teachers": x.get("teachers", []), "status": x.get("status"),
                            "changes": x.get("changes", []), "topic": topic, "homework": homework,
                            "materials": mats, "assignments": tasks, "attendance": attendance,
                            "attendance_label": att_label,
                            "unviewed": sum(1 for m in mats if not m.get("viewed"))})
    extra = [it for d, lst in sorted(by_date.items(), reverse=True) if d not in used for it in lst]
    return {"from": d0.isoformat(), "to": end.isoformat(), "lessons": out_lessons, "other_materials": extra,
            "student_id": sid, "register": show_register,
            "unviewed": sum(1 for it in items if not it.get("viewed"))}


# Aufgaben & Abgaben (Abgabe, Bewertung, Raster, Fristverlängerung, Gruppen): ``features_assignments.py``


# =========================================================================== Pinnwand
def _post_out(post: ChannelPost, ctx: Ctx, infos: dict[str, dict], teacher_users: set[int],
              replies: Optional[list[dict]] = None) -> dict[str, Any]:
    deleted = post.deleted_at is not None
    own = post.author_id == ctx.user.id
    active = not ctx.ch.archived
    return {
        "id": post.id, "parent_id": post.parent_id, "author_name": post.author_name or "Unbekannt",
        "author_is_teacher": post.author_id in teacher_users, "own": own,
        "body": "" if deleted else post.read_text("body"), "deleted": deleted, "pinned": bool(post.pinned),
        "created_at": iso(post.created_at), "edited_at": iso(post.edited_at),
        "attachments": [] if deleted else [infos[i] for i in post.attachment_ids or [] if i in infos],
        "can_edit": own and not deleted and active and not ctx.supervisor,
        "can_delete": not deleted and active and (own or ctx.teacher),
        "can_pin": ctx.teacher and active and post.parent_id is None and not deleted,
        **({"replies": replies} if replies is not None else {}),
    }


def _teacher_user_ids(db: Session, ctx: Ctx, author_ids: Iterable[Optional[int]]) -> set[int]:
    ids = {a for a in author_ids if a}
    if not ids:
        return set()
    tids = set(ctx.spec.teacher_ids) if ctx.spec else set()
    out: set[int] = set()
    for chunk in _chunks(sorted(ids)):
        for uid, tid in db.execute(select(User.id, User.teacher_id).where(User.id.in_(chunk))):
            if tid and tid in tids:
                out.add(uid)
        out.update(db.scalars(select(ChannelExtraMember.user_id).where(
            ChannelExtraMember.channel_id == ctx.ch.id, ChannelExtraMember.role == TEACHER,
            ChannelExtraMember.user_id.in_(chunk))))
    return out


def _get_post(db: Session, ctx: Ctx, post_id: int) -> ChannelPost:
    post = db.get(ChannelPost, post_id)
    if post is None or post.channel_id != ctx.ch.id or post.deleted_at is not None:
        raise HTTPException(404, "Beitrag nicht gefunden")
    return post


@router.get("/channels/{channel_id}/posts")
def list_posts(channel_id: int, limit: int = Query(50, ge=1, le=200), before: Optional[int] = None,
               student_id: Optional[str] = Query(None, max_length=40),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Pinnwand: angeheftete Beiträge zuerst, dann die neuesten (``before`` = ältere nachladen), Antworten je
    Beitrag aufsteigend. Eltern lesen mit, schreiben nicht."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    base = select(ChannelPost).where(ChannelPost.channel_id == ctx.ch.id, ChannelPost.parent_id.is_(None))
    pinned = [] if before else list(db.scalars(base.where(ChannelPost.pinned.is_(True),
                                                          ChannelPost.deleted_at.is_(None))
                                               .order_by(ChannelPost.created_at.desc())))
    stmt = base.where(ChannelPost.pinned.is_(False) | ChannelPost.deleted_at.is_not(None))
    if before:
        stmt = stmt.where(ChannelPost.id < before)
    rest = list(db.scalars(stmt.order_by(ChannelPost.id.desc()).limit(limit + 1)))
    has_more = len(rest) > limit
    rest = rest[:limit]
    tops = [*pinned, *rest]
    replies: dict[int, list[ChannelPost]] = defaultdict(list)
    for chunk in _chunks([p.id for p in tops]):
        for r in db.scalars(select(ChannelPost).where(ChannelPost.parent_id.in_(chunk), ChannelPost.deleted_at.is_(None))
                            .order_by(ChannelPost.created_at, ChannelPost.id)):
            replies[r.parent_id or 0].append(r)
    all_posts = [*tops, *(r for lst in replies.values() for r in lst)]
    infos = {f["id"]: f for f in files.files_info(
        db, [i for p in all_posts if p.deleted_at is None for i in p.attachment_ids or []], user, check_access=False)}
    teachers = _teacher_user_ids(db, ctx, (p.author_id for p in all_posts))
    out = []
    for p in tops:
        reps = [_post_out(r, ctx, infos, teachers) for r in replies.get(p.id, [])]
        if p.deleted_at is not None and not reps:
            continue
        out.append(_post_out(p, ctx, infos, teachers, reps))
    return {"posts": out, "has_more": has_more, "next_before": rest[-1].id if has_more and rest else None,
            "permissions": _permissions_out(ctx)}


@router.post("/channels/{channel_id}/posts", status_code=201)
def create_post(channel_id: int, body: PostIn, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Beitrag oder Antwort (eine Ebene); Teilnehmende nur, wenn der Kursraum es erlaubt."""
    ctx = _ctx(db, user, channel_id, write=True)
    parent = None
    if body.parent_id is not None:
        parent = _get_post(db, ctx, body.parent_id)
        if parent.parent_id is not None:
            raise HTTPException(422, "Antworten sind nur auf Beiträge möglich, nicht auf Antworten")
    if ctx.student:
        if parent is None and not ctx.ch.setting("students_can_post"):
            raise HTTPException(403, "In diesem Kursraum schreiben nur die Lehrenden neue Beiträge")
        if parent is not None and not ctx.ch.setting("students_can_reply"):
            raise HTTPException(403, "In diesem Kursraum sind Antworten von Teilnehmenden ausgeschaltet")
    text = logic.clean_text(body.body, MAX_POST)
    if not text:
        raise HTTPException(422, "Der Beitrag ist leer")
    limit, minutes = POST_RATE
    recent = int(db.scalar(select(func.count()).select_from(ChannelPost).where(
        ChannelPost.author_id == user.id, ChannelPost.created_at > utcnow() - timedelta(minutes=minutes))) or 0)
    if recent >= limit:
        raise HTTPException(429, "Sie haben gerade sehr viele Beiträge geschrieben – bitte kurz warten")
    post = ChannelPost(channel_id=ctx.ch.id, parent_id=parent.id if parent else None, author_id=user.id,
                       author_name=(user.display_name or user.username)[:200], pinned=False, created_at=utcnow(),
                       body_enc="")
    db.add(post)
    db.flush()
    post.write_text("body", text)
    if body.attachment_ids:
        ids = list(dict.fromkeys(body.attachment_ids))
        files.attach_many(db, ids, user, REF_POST, post.id, max_files=MAX_POST_ATTACHMENTS)
        post.attachment_ids = ids
    db.commit()
    _notify(db, ctx)
    infos = {f["id"]: f for f in files.files_info(db, post.attachment_ids or [], user, check_access=False)}
    teachers = _teacher_user_ids(db, ctx, [user.id])
    return _post_out(post, ctx, infos, teachers, [] if parent is None else None)


@router.patch("/channels/{channel_id}/posts/{post_id}")
def patch_post(channel_id: int, post_id: int, body: PostPatch, request: Request,
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eigenen Beitrag bearbeiten; Anheften/Lösen (Lehrende, nur Beiträge der obersten Ebene)."""
    ctx = _ctx(db, user, channel_id, write=True)
    post = _get_post(db, ctx, post_id)
    if body.body is not None:
        if post.author_id != user.id:
            raise HTTPException(403, "Nur eigene Beiträge lassen sich bearbeiten")
        text = logic.clean_text(body.body, MAX_POST)
        if not text:
            raise HTTPException(422, "Der Beitrag ist leer")
        post.write_text("body", text)
        post.edited_at = utcnow()
    if body.pinned is not None:
        if not ctx.teacher:
            raise HTTPException(403, "Anheften dürfen nur Lehrende")
        if post.parent_id is not None:
            raise HTTPException(422, "Nur Beiträge (keine Antworten) lassen sich anheften")
        if bool(post.pinned) != body.pinned:
            post.pinned = body.pinned
            audit(db, user, "channel_post.pin" if body.pinned else "channel_post.unpin", f"channel_post:{post.id}",
                  {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    infos = {f["id"]: f for f in files.files_info(db, post.attachment_ids or [], user, check_access=False)}
    return _post_out(post, ctx, infos, _teacher_user_ids(db, ctx, [post.author_id]))


@router.delete("/channels/{channel_id}/posts/{post_id}")
def delete_post(channel_id: int, post_id: int, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Eigenen Beitrag löschen; Lehrende moderieren (löschen fremde Beiträge – bei Beiträgen samt Antworten)."""
    ctx = _ctx(db, user, channel_id, write=True)
    post = _get_post(db, ctx, post_id)
    own = post.author_id == user.id
    if not own and not ctx.teacher:
        raise HTTPException(403, "Nur eigene Beiträge lassen sich löschen")
    now = utcnow()
    targets = [post]
    if ctx.teacher and post.parent_id is None and not own:
        targets += list(db.scalars(select(ChannelPost).where(ChannelPost.parent_id == post.id,
                                                             ChannelPost.deleted_at.is_(None))))
    for p in targets:
        files.delete_for_ref(db, REF_POST, p.id, hard=True)
        p.body_enc = ""
        p.attachment_ids = None
        p.pinned = False
        p.deleted_at = now
    audit(db, user, "channel_post.delete" if own else "channel_post.moderate", f"channel_post:{post.id}",
          {"channel_id": ctx.ch.id, "posts": len(targets), "author_id": post.author_id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"deleted": post_id, "count": len(targets)}


# =========================================================================== Hausaufgaben im Stundenplan
def homework_due(db: Session, user: Any, snap: Any, kind: str, ref: str, d1: date, d2: date) -> dict[str, list[dict]]:
    """Fällige Aufgaben (Hausaufgaben) der Kursräume einer Ansicht im Zeitraum ``[d1, d2]`` (Ortszeit), je Tag.

    Klasse: Kursteile der Klasse + Klassenraum; Lehrkraft: eigene Kursräume; Schüler/in: eigene Kursräume
    (Zusatzmitgliedschaften ja, ausgetragen nein); Raum: keine. Nur freigegebene Aufgaben; Schüler/innen (und Eltern
    in der Schüleransicht) sehen den eigenen Abgabestatus – nie Abgaben anderer. ``can_open``: Betrachter darf den
    Kursraum öffnen (sonst kein Link). Lehrende des Kursraums sehen ``submitted``/``expected`` (Abgaben)."""
    from zoneinfo import ZoneInfo

    school = snap[1]
    if kind == "room":
        return {}
    if kind == "class":
        idx = logic.index_for(school)
        specs = [s for s in logic.all_specs(school) if ref in s.class_ids]
        spec = logic.class_spec(idx, ref)
        if spec is not None and spec not in specs:
            specs.append(spec)
    elif kind == "teacher":
        specs = logic.teacher_specs(school, ref)
    else:
        specs = logic.student_specs(school, ref)
    rows = _ensure_rows(db, specs)
    channels: dict[int, tuple[Channel, Optional[logic.ChannelSpec]]] = {
        row.id: (row, spec) for spec in specs if (row := rows.get((spec.kind, spec.ref))) is not None}
    pupil_uid: Optional[int] = None
    if kind == "student":
        pupil_uid = db.scalar(select(User.id).where(User.student_id == ref, User.role == "schueler",
                                                    User.active.is_(True)).order_by(User.id).limit(1))
        if pupil_uid:
            for ch_id, role in db.execute(select(ChannelExtraMember.channel_id, ChannelExtraMember.role)
                                          .where(ChannelExtraMember.user_id == pupil_uid)):
                if role == EXCLUDED:
                    channels.pop(ch_id, None)
                elif ch_id not in channels:
                    ch = db.get(Channel, ch_id)
                    if ch is not None:
                        channels[ch_id] = (ch, _spec_for(school, ch))
    if not channels:
        return {}
    tz = ZoneInfo("Europe/Berlin")
    start = datetime.combine(d1, datetime.min.time(), tz).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(d2 + timedelta(days=1), datetime.min.time(), tz).astimezone(timezone.utc).replace(
        tzinfo=None)
    items = list(db.scalars(select(ChannelItem).where(
        ChannelItem.channel_id.in_(list(channels)), ChannelItem.type == "assignment",
        ChannelItem.due_at.is_not(None), ChannelItem.due_at >= start, ChannelItem.due_at < end)))
    if not items:
        return {}
    clock = Clock(snap)
    if kind == "student" or getattr(user, "role", "") in ("schueler", "eltern"):
        who_uid = pupil_uid if kind == "student" else (user.id if getattr(user, "role", "") == "schueler" else None)
        clock.restrict(db, None, list(channels), who_uid)
    states_by_channel: dict[int, dict[int, logic.Visibility]] = {}
    subs: dict[int, AssignmentSubmission] = {}
    if pupil_uid:
        subs = {s.item_id: s for s in db.scalars(select(AssignmentSubmission).where(
            AssignmentSubmission.student_user_id == pupil_uid,
            AssignmentSubmission.item_id.in_([i.id for i in items])))}
    hw_ovr = at.due_overrides(db, [i.id for i in items], pupil_uid) if pupil_uid else {}
    idx = logic.index_for(school)
    roles: dict[int, Optional[str]] = {}
    counts: dict[int, int] = {}
    for it in items:
        if it.channel_id not in roles:
            ch0, spec0 = channels[it.channel_id]
            roles[it.channel_id] = _role_for(db, user, ch0, spec0, school)
    teacher_items = [it.id for it in items if roles.get(it.channel_id) == TEACHER]
    if teacher_items:
        counts = dict(db.execute(select(AssignmentSubmission.item_id, func.count(AssignmentSubmission.id))
                                 .where(AssignmentSubmission.item_id.in_(teacher_items),
                                        AssignmentSubmission.submitted_at.is_not(None))
                                 .group_by(AssignmentSubmission.item_id)).all())
    out: dict[str, list[dict]] = {}
    for it in items:
        if it.channel_id not in states_by_channel:
            states_by_channel[it.channel_id] = clock.folder_states(_folders(db, it.channel_id))
        if not clock.visibility(it, states_by_channel[it.channel_id]).visible:
            continue
        ch, spec = channels[it.channel_id]
        local = it.due_at.replace(tzinfo=timezone.utc).astimezone(tz)
        entry: dict[str, Any] = {"item_id": it.id, "channel_id": ch.id, "channel_title": ch.title, "title": it.title,
                                 "due_at": iso(it.due_at), "time": local.strftime("%H:%M"),
                                 "subject": spec.subject if spec is not None else None,
                                 "subject_name": idx.subject_name(spec.subject) if spec is not None and spec.subject
                                 else None, "can_open": roles.get(it.channel_id) is not None,
                                 "created_at": iso(it.created_at),
                                 "course_id": spec.course_id if spec is not None else None,
                                 "part": spec.part if spec is not None else None,
                                 "class_teacher": spec.class_teacher if spec is not None else None}
        if roles.get(it.channel_id) == TEACHER and spec is not None:
            entry["submitted"] = counts.get(it.id, 0)
            entry["expected"] = len(logic.channel_student_ids(school, spec.kind, spec.ref))
        if kind == "student":
            sub = subs.get(it.id)
            status = logic.submission_status(at.effective_due(it.due_at, hw_ovr.get(it.id)),
                                             sub.submitted_at if sub else None, sub.status if sub else None, clock.now)
            entry["status"] = status
            entry["status_label"] = logic.SUBMISSION_LABELS.get(status, status)
        out.setdefault(local.date().isoformat(), []).append(entry)
    for lst in out.values():
        lst.sort(key=lambda e: (e["time"], e["title"]))
    return out
