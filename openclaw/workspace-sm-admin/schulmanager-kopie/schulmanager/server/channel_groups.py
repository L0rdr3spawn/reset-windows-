"""Gruppen im Kursraum – Abfragen und Schnittstelle für die Sichtbarkeit (Tabellen: ``feature_models/channel_groups.py``).

Schnittstelle für „bedingte Freigabe nach Gruppe“ (M2) und andere Module
------------------------------------------------------------------------
* :func:`user_group_ids` – Gruppen-IDs, in denen ein Konto in einem Kursraum Mitglied ist.
* :func:`user_in_any_group` – ``True``, wenn das Konto in mindestens einer der Gruppen ist (leere Liste = „für alle“).
* :func:`item_group_ids` / :func:`folder_group_ids` – Gruppen, auf die Material/Ordner beschränkt ist (leer = alle).
* :func:`item_allowed` – Wahrheitswert „darf dieses Konto das Material sehen?“ (nur Gruppen-Bedingung, ohne
  Datum/Stunde); Lehrende sind nie betroffen.
* :func:`blocked_for` – alle wegen der Gruppe gesperrten Material-/Ordner-IDs eines Kontos (für Listen).
* REST: ``GET/PUT /channels/{id}/items/{item_id}/groups`` und ``/folders/{folder_id}/groups``.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .feature_models.channel_groups import ChannelGroup, ChannelGroupGate, ChannelGroupMember, ChannelGroupSet


@dataclass
class Blocked:
    """Material und Ordner, die ein Konto wegen einer Gruppen-Beschränkung nicht sehen darf."""
    items: set[int] = field(default_factory=set)
    folders: set[int] = field(default_factory=set)

    def __bool__(self) -> bool:
        return bool(self.items or self.folders)


def user_group_ids(db: Session, channel_id: int, user_id: Optional[int]) -> set[int]:
    if not user_id:
        return set()
    return set(db.scalars(select(ChannelGroupMember.group_id).where(
        ChannelGroupMember.channel_id == channel_id, ChannelGroupMember.user_id == user_id)))


def is_member(db: Session, group_id: Optional[int], user_id: Optional[int]) -> bool:
    if not group_id or not user_id:
        return False
    return db.scalar(select(ChannelGroupMember.id).where(
        ChannelGroupMember.group_id == group_id, ChannelGroupMember.user_id == user_id).limit(1)) is not None


def user_in_any_group(db: Session, channel_id: int, user_id: Optional[int], group_ids: Iterable[int]) -> bool:
    """Mitglied in mindestens einer der Gruppen? Leere Auswahl = Bedingung entfällt (``True``)."""
    wanted = set(group_ids)
    return not wanted or bool(wanted & user_group_ids(db, channel_id, user_id))


def gate_map(db: Session, channel_ids: Iterable[int]) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    """``(Material-ID → Gruppen, Ordner-ID → Gruppen)`` der Kanäle."""
    ids = sorted(set(channel_ids))
    items: dict[int, set[int]] = defaultdict(set)
    folders: dict[int, set[int]] = defaultdict(set)
    if not ids:
        return items, folders
    for item_id, folder_id, group_id in db.execute(
            select(ChannelGroupGate.item_id, ChannelGroupGate.folder_id, ChannelGroupGate.group_id)
            .where(ChannelGroupGate.channel_id.in_(ids))):
        if item_id is not None:
            items[item_id].add(group_id)
        elif folder_id is not None:
            folders[folder_id].add(group_id)
    return items, folders


def item_group_ids(db: Session, item_id: int) -> list[int]:
    return sorted(db.scalars(select(ChannelGroupGate.group_id).where(ChannelGroupGate.item_id == item_id)))


def folder_group_ids(db: Session, folder_id: int) -> list[int]:
    return sorted(db.scalars(select(ChannelGroupGate.group_id).where(ChannelGroupGate.folder_id == folder_id)))


def blocked_for(db: Session, channel_ids: Iterable[int], user_id: Optional[int]) -> Blocked:
    """Gesperrtes Material/Ordner für ``user_id`` (Schüler/in bzw. Kind) in den Kanälen."""
    ids = sorted(set(channel_ids))
    out = Blocked()
    if not ids:
        return out
    items, folders = gate_map(db, ids)
    if not items and not folders:
        return out
    mine: set[int] = set()
    if user_id:
        mine = set(db.scalars(select(ChannelGroupMember.group_id).where(
            ChannelGroupMember.channel_id.in_(ids), ChannelGroupMember.user_id == user_id)))
    out.items = {i for i, groups in items.items() if not groups & mine}
    out.folders = {f for f, groups in folders.items() if not groups & mine}
    return out


def item_allowed(db: Session, channel_id: int, item_id: int, user_id: Optional[int]) -> bool:
    groups = item_group_ids(db, item_id)
    return not groups or bool(set(groups) & user_group_ids(db, channel_id, user_id))


def set_gate(db: Session, channel_id: int, group_ids: Iterable[int], *, item_id: Optional[int] = None,
             folder_id: Optional[int] = None) -> list[int]:
    """Ersetzt die Gruppen-Beschränkung eines Materials/Ordners (leere Liste = für alle). Ungültige Gruppen fallen weg."""
    if (item_id is None) == (folder_id is None):
        raise ValueError("entweder Material oder Ordner")
    valid = set(db.scalars(select(ChannelGroup.id).where(ChannelGroup.channel_id == channel_id,
                                                         ChannelGroup.id.in_(list(set(group_ids)) or [0]))))
    col = ChannelGroupGate.item_id if item_id is not None else ChannelGroupGate.folder_id
    db.execute(delete(ChannelGroupGate).where(col == (item_id if item_id is not None else folder_id)))
    for gid in sorted(valid):
        db.add(ChannelGroupGate(channel_id=channel_id, group_id=gid, item_id=item_id, folder_id=folder_id))
    db.flush()
    return sorted(valid)


def members_of(db: Session, group_id: int) -> list[int]:
    return list(db.scalars(select(ChannelGroupMember.user_id).where(ChannelGroupMember.group_id == group_id)
                           .order_by(ChannelGroupMember.id)))


def group_of_user(db: Session, set_id: Optional[int], user_id: Optional[int]) -> Optional[ChannelGroup]:
    """Gruppe des Kontos in einer Einteilung (``None`` = in keiner Gruppe)."""
    if not set_id or not user_id:
        return None
    return db.scalar(select(ChannelGroup).join(ChannelGroupMember, ChannelGroupMember.group_id == ChannelGroup.id)
                     .where(ChannelGroupMember.set_id == set_id, ChannelGroupMember.user_id == user_id))


def set_exists(db: Session, channel_id: int, set_id: int) -> bool:
    row = db.get(ChannelGroupSet, set_id)
    return row is not None and row.channel_id == channel_id
