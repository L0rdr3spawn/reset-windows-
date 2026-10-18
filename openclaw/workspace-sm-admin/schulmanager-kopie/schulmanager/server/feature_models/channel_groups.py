"""Gruppen innerhalb eines Kursraums (Migration 0036).

* ``channel_group_sets`` – eine **Einteilung** („Projektgruppen“, „Niveaustufen“); je Einteilung gehört jedes Mitglied
  zu höchstens einer Gruppe.
* ``channel_groups`` – Gruppen einer Einteilung.
* ``channel_group_members`` – Schüler/innen-Konten in Gruppen (``set_id`` + ``user_id`` eindeutig).
* ``channel_group_gates`` – Sichtbarkeit: Material (``item_id``) oder Ordner (``folder_id``) ist nur für Mitglieder
  der eingetragenen Gruppen sichtbar (ohne Eintrag: für alle). Lehrende sehen immer alles.

Schnittstelle für „bedingte Freigabe nach Gruppe“: ``schulmanager.server.channel_groups``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class ChannelGroupSet(Base):
    __tablename__ = "channel_group_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChannelGroup(Base):
    __tablename__ = "channel_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    set_id: Mapped[int] = mapped_column(ForeignKey("channel_group_sets.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChannelGroupMember(Base):
    __tablename__ = "channel_group_members"
    __table_args__ = (UniqueConstraint("set_id", "user_id", name="uq_channel_group_members_set_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    set_id: Mapped[int] = mapped_column(ForeignKey("channel_group_sets.id", ondelete="CASCADE"))
    group_id: Mapped[int] = mapped_column(ForeignKey("channel_groups.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChannelGroupGate(Base):
    """Material/Ordner nur für bestimmte Gruppen (genau eines von ``item_id``/``folder_id`` ist gesetzt)."""
    __tablename__ = "channel_group_gates"
    __table_args__ = (UniqueConstraint("group_id", "item_id", name="uq_channel_group_gates_group_item"),
                      UniqueConstraint("group_id", "folder_id", name="uq_channel_group_gates_group_folder"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("channel_groups.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_items.id", ondelete="CASCADE"),
                                                   nullable=True, index=True)
    folder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_folders.id", ondelete="CASCADE"),
                                                     nullable=True, index=True)
