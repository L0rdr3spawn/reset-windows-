"""Kursräume (Agent Kursräume, ARCHITECTURE.md §9.4) – Kanäle, Ordner, Material, Aufgaben, Abgaben, Pinnwand.

Tabellen
--------
* ``channels`` – ein Kanal je Kursteil (``kind="course"``, ``ref="<kurs>#<teil>"``), je Klasse (``kind="class"``,
  ``ref=<klasse>``) oder frei angelegt (``kind="custom"``, ``ref=NULL``). Kurs-/Klassenkanäle werden bei Bedarf
  angelegt; ihre Mitglieder ergeben sich **dynamisch** aus dem Planungsdokument (``schulmanager/channels.py``).
  ``settings`` = ``{"students_can_post": bool, "students_can_reply": bool}``.
* ``channel_extra_members`` – zusätzliche Mitglieder (``role`` = ``teacher|student``), z. B. Referendar/in.
* ``channel_folders`` – verschachtelte Ordner (``parent_id``), sortierbar (``position``), mit eigener Freigabe
  (``visibility`` wie beim Material, ``NULL`` = alt: nur ``hidden``; ``hidden`` bleibt = ``visibility == "hidden"``).
* ``channel_items`` – Material: ``type`` = ``file|link|text|assignment``; Sichtbarkeit ``visibility`` =
  ``visible|hidden|scheduled|lesson`` (``visible_from`` UTC; zur Unterrichtsstunde: ``lesson_date``/``lesson_id``/
  ``lesson_period``, sichtbar ab Stundenbeginn laut ``settings.period_times``), Aufgaben mit ``due_at`` (UTC).
* ``assignment_submissions`` – Abgaben (Text + Dateien) mit Status ``abgegeben|verspaetet|bewertet|zurueckgegeben``,
  Rückmeldung und Bewertung.
* ``channel_posts`` – Pinnwand mit Antworten (``parent_id``, eine Ebene), Anheften, weiches Löschen.
* Papierkorb: ``channel_items``/``channel_folders`` tragen ``deleted_at``/``deleted_by``/``trash_group``; gelöschte Zeilen
  bleiben samt Abgaben und Dateien bestehen, sind aber für alle Abfragen unsichtbar (:func:`_hide_trashed`).
* ``channel_reads`` – letzter Besuch je Konto und Kanal (für „Neues Material“).

Freitexte (Textseiten/Aufgabentexte, Abgabetexte, Rückmeldungen, Bewertungen, Pinnwand-Beiträge) werden nur
**verschlüsselt** gespeichert (``crypto.encrypt_text``, AAD ``<tabelle>.<feld>:<id>``, Spalten ``*_enc``) –
gelesen/geschrieben über :meth:`EncryptedText.read_text`/:meth:`EncryptedText.write_text` (ID vorher per
``db.flush()`` erzeugen). Zeitstempel sind naive UTC (``db.utcnow``).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, event,
                        false)
from sqlalchemy.orm import Mapped, Session, mapped_column, with_loader_criteria

from ..db import Base, utcnow

log = logging.getLogger("schulmanager.channels")

CHANNEL_KINDS = ("course", "class", "custom")
ITEM_TYPES = ("file", "link", "text", "assignment")
VISIBILITIES = ("visible", "hidden", "scheduled", "lesson")
MEMBER_ROLES = ("teacher", "student")
SUBMISSION_STATUSES = ("abgegeben", "verspaetet", "bewertet", "zurueckgegeben")
DEFAULT_SETTINGS: dict[str, Any] = {"students_can_post": True, "students_can_reply": True, "progress_parents": False}
UNREADABLE = "[nicht lesbar]"


class EncryptedText:
    """Mixin: verschlüsselte Textspalten ``<feld>_enc`` mit AAD ``<tabelle>.<feld>:<id>``."""

    def text_aad(self, field: str) -> str:
        return f"{getattr(self, '__tablename__', '')}.{field}:{getattr(self, 'id', None)}"

    def read_text(self, field: str) -> str:
        """Klartext des Felds (leer, wenn nichts gespeichert; ``[nicht lesbar]`` bei Schlüssel-/Datenfehlern)."""
        token = getattr(self, f"{field}_enc", "") or ""
        if not token:
            return ""
        from .. import crypto

        try:
            return crypto.decrypt_text(token, self.text_aad(field))
        except crypto.CryptoError:
            log.warning("%s lässt sich nicht entschlüsseln", self.text_aad(field))
            return UNREADABLE

    def write_text(self, field: str, value: str | None) -> None:
        """Speichert ``value`` verschlüsselt (leere Texte bleiben leer). Die Zeile braucht bereits ihre ID."""
        from .. import crypto

        value = value or ""
        if value and not getattr(self, "id", None):
            raise ValueError(f"{self.text_aad(field)}: ID muss vor dem verschlüsselten Feld feststehen (flush)")
        setattr(self, f"{field}_enc", crypto.encrypt_text(value, self.text_aad(field)) if value else "")


class Channel(Base):
    """Kanal (Kursraum) eines Kursteils, einer Klasse oder frei angelegt."""
    __tablename__ = "channels"
    __table_args__ = (UniqueConstraint("kind", "ref", name="uq_channels_kind_ref"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)                  # course|class|custom
    ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # "<kurs>#<teil>" | <klasse> | NULL
    title: Mapped[str] = mapped_column(String(200), default="")                 # custom; sonst letzter bekannter Titel
    description: Mapped[str] = mapped_column(Text, default="")
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def setting(self, key: str) -> Any:
        return {**DEFAULT_SETTINGS, **(self.settings or {})}.get(key)


class ChannelExtraMember(Base):
    """Zusätzliches Mitglied eines Kanals (nur ``channels.manage`` ohne Einschränkung legt sie an)."""
    __tablename__ = "channel_extra_members"
    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_channel_extra_members_channel_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="student")            # teacher|student
    added_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChannelFolder(Base):
    """Ordner (verschachtelt über ``parent_id``)."""
    __tablename__ = "channel_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_folders.id", ondelete="CASCADE"),
                                                     nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer, default=0)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    # Freigabe des ganzen Ordners (0013): visible|hidden|scheduled|lesson; NULL = nur ``hidden`` (alte Zeilen)
    visibility: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    visible_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # UTC
    lesson_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    lesson_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Papierkorb (0037): gelöscht = ``deleted_at`` gesetzt; ``trash_group`` verbindet alles, was zusammen gelöscht wurde
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # Konto (ohne Fremdschlüssel)
    trash_group: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    @property
    def effective_visibility(self) -> str:
        return "hidden" if self.hidden else (self.visibility or "visible")


class ChannelItem(EncryptedText, Base):
    """Material (Datei, Link, Textseite) oder Aufgabe."""
    __tablename__ = "channel_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    folder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_folders.id", ondelete="CASCADE"),
                                                     nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(20))                               # file|link|text|assignment
    title: Mapped[str] = mapped_column(String(200))
    body_enc: Mapped[str] = mapped_column(Text, default="")                     # Markdown, verschlüsselt
    url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(ForeignKey("stored_files.id", ondelete="SET NULL"),
                                                   nullable=True)
    attachment_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="visible")      # visible|hidden|scheduled|lesson
    visible_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # UTC
    lesson_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    lesson_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)         # UTC
    allow_late: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Unterrichtsmaterial: erscheint im Bereich „Unterricht“ beim Datum der Stunde (für Nachholende)
    lesson_material: Mapped[bool] = mapped_column(Boolean, default=False)
    material_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    # Abgabe möglich (auch bei Material, das keine Aufgabe ist)
    submittable: Mapped[bool] = mapped_column(Boolean, default=False)
    # Klassenraum: angeheftete Infokarte (Bereich „Klasse“), erscheint nicht unter Material
    info_card: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Papierkorb (0037), siehe :class:`ChannelFolder`
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # Konto (ohne Fremdschlüssel)
    trash_group: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)


class AssignmentSubmission(EncryptedText, Base):
    """Abgabe einer Schülerin/eines Schülers zu einer Aufgabe."""
    __tablename__ = "assignment_submissions"
    __table_args__ = (UniqueConstraint("item_id", "student_user_id", name="uq_assignment_submissions_item_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("channel_items.id", ondelete="CASCADE"), index=True)
    student_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    text_enc: Mapped[str] = mapped_column(Text, default="")
    file_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="abgegeben")
    feedback_enc: Mapped[str] = mapped_column(Text, default="")
    grade_enc: Mapped[str] = mapped_column(Text, default="")
    feedback_file_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    feedback_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Aufgaben-Erweiterungen (Migration 0036, ``feature_models/assignments.py``):
    # Version/Versuch (1 = erste Abgabe; „Überarbeitung anfordern“ legt eine neue Version an), Gruppenabgabe
    # (``group_id``: jedes Mitglied hat eine Zeile mit demselben Inhalt), Punkte, ausgefülltes
    # Bewertungsraster (verschlüsselt) und Einzelanpassung einer Gruppenbewertung.
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rubric_enc: Mapped[str] = mapped_column(Text, default="")
    individual: Mapped[bool] = mapped_column(Boolean, default=False)
    revision_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # Frist der Überarbeitung (UTC)


class ChannelPost(EncryptedText, Base):
    """Beitrag auf der Pinnwand (``parent_id`` = Antwort auf einen Beitrag)."""
    __tablename__ = "channel_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_posts.id", ondelete="CASCADE"),
                                                     nullable=True, index=True)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                     index=True)
    author_name: Mapped[str] = mapped_column(String(200), default="")
    body_enc: Mapped[str] = mapped_column(Text, default="")
    attachment_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ChannelRead(Base):
    """Letzter Besuch eines Kontos in einem Kanal (Hervorhebung „neu“)."""
    __tablename__ = "channel_reads"
    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_channel_reads_channel_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChannelItemView(Base):
    """Material, das ein Konto schon geöffnet hat (Bereich „Unterricht“: Hinweis auf noch nicht angesehenes Material)."""
    __tablename__ = "channel_item_views"
    __table_args__ = (UniqueConstraint("item_id", "user_id", name="uq_channel_item_views_item_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("channel_items.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


@event.listens_for(Session, "do_orm_execute")
def _hide_trashed(state) -> None:
    """Gelöschte Kursraum-Elemente (Papierkorb) sind für jede Abfrage unsichtbar – außer mit
    ``execution_options={"include_trashed": True}`` (Papierkorb, Wiederherstellen, endgültiges Löschen)."""
    if state.is_select and not state.execution_options.get("include_trashed"):
        state.statement = state.statement.options(
            with_loader_criteria(ChannelItem, ChannelItem.deleted_at.is_(None), include_aliases=True),
            with_loader_criteria(ChannelFolder, ChannelFolder.deleted_at.is_(None), include_aliases=True))


Index("ix_channel_items_channel_lesson", ChannelItem.channel_id, ChannelItem.lesson_date)

ENCRYPTED_COLUMNS: tuple[tuple[type, str], ...] = (
    (ChannelItem, "body_enc"),
    (AssignmentSubmission, "text_enc"),
    (AssignmentSubmission, "feedback_enc"),
    (AssignmentSubmission, "grade_enc"),
    (AssignmentSubmission, "rubric_enc"),
    (ChannelPost, "body_enc"),
)


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): verschlüsselte Texte der Kursräume neu verpacken."""
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover - Basisdienst fehlt
        return
    for model, column in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"{model.__tablename__}.{column}",
                               lambda db, model=model, column=column: crypto.rewrap_column(db, model, column))


_register_rewrap()
