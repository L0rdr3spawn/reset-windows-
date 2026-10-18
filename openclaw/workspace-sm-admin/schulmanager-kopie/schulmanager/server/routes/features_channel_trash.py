"""Papierkorb der Kursräume (Moodle-Lücken M2, ``docs/LERNFORTSCHRITT.md``).

Löschen von Material, Aufgaben und Ordnern (``DELETE /channels/{id}/items/{iid}`` bzw. ``/folders/{fid}``) legt sie hier
ab, statt sie zu vernichten: Abgaben, Dateien, Abschluss- und Freigaberegeln bleiben erhalten, die Zeilen sind für alle
Abfragen unsichtbar (``feature_models.channels._hide_trashed``). Was zusammen gelöscht wurde, teilt sich eine
``trash_group``; Wiederherstellen und endgültiges Löschen wirken auf die ganze Gruppe.

* ``GET    /channels/{id}/trash`` – Lehrende: Einträge mit Löschzeit, „löscht sich am …“ und den eigenen Möglichkeiten.
* ``POST   /channels/{id}/trash/{group}/restore`` – wiederherstellen (Recht ``channels.trash`` + Bearbeitungsrecht
  am Material; in Klassenräumen nur eigenes bzw. Klassenleitung/Verwaltung). Fehlt der ursprüngliche Ordner, landet das
  Material oben im Kursraum; ein gleichnamiger Ordner bekommt „(2)“.
* ``DELETE /channels/{id}/trash/{group}`` – endgültig löschen (gleiches Recht); ``DELETE /channels/{id}/trash`` leert
  den Papierkorb (soweit erlaubt).
* Frist: ``settings.trash_retention_days`` (Standard 30 Tage, 1–365; ``PUT /settings``). :func:`run_purge` löscht
  Abgelaufenes endgültig und läuft in der Wartung (``maintenance.run_maintenance``).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager.server import assignment_tools, progress
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, session_scope, utcnow
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.feature_models.channels import AssignmentSubmission, ChannelFolder, ChannelItem
from schulmanager.server.store import get_store

from . import features_channels as fc
from .features_common import has

log = logging.getLogger("schulmanager.channels")
router = APIRouter(tags=["Kursräume"])

DEFAULT_RETENTION_DAYS = 30
TRASHED = {"include_trashed": True}


def retention_days() -> int:
    try:
        days = int(getattr(get_store().school.settings, "trash_retention_days", DEFAULT_RETENTION_DAYS)
                   or DEFAULT_RETENTION_DAYS)
    except Exception:  # noqa: BLE001 - ohne Planungsdokument gilt der Standard
        days = DEFAULT_RETENTION_DAYS
    return max(1, min(days, 365))


def _trashed_items(db: Session, **where: Any) -> list[ChannelItem]:
    stmt = select(ChannelItem).where(ChannelItem.deleted_at.is_not(None))
    for key, value in where.items():
        stmt = stmt.where(getattr(ChannelItem, key) == value)
    return list(db.scalars(stmt, execution_options=TRASHED))


def _trashed_folders(db: Session, **where: Any) -> list[ChannelFolder]:
    stmt = select(ChannelFolder).where(ChannelFolder.deleted_at.is_not(None))
    for key, value in where.items():
        stmt = stmt.where(getattr(ChannelFolder, key) == value)
    return list(db.scalars(stmt, execution_options=TRASHED))


def _groups(db: Session, channel_id: int) -> dict[str, dict[str, list[Any]]]:
    out: dict[str, dict[str, list[Any]]] = {}
    for item in _trashed_items(db, channel_id=channel_id):
        out.setdefault(item.trash_group or f"item{item.id}", {"items": [], "folders": []})["items"].append(item)
    for folder in _trashed_folders(db, channel_id=channel_id):
        out.setdefault(folder.trash_group or f"folder{folder.id}", {"items": [], "folders": []})["folders"].append(folder)
    return out


def _roots(group: dict[str, list[Any]]) -> tuple[list[ChannelFolder], list[ChannelItem]]:
    """Oberste Einträge einer Löschaktion: Ordner ohne Elternordner in der Gruppe, Material ohne Ordner in der Gruppe."""
    fids = {f.id for f in group["folders"]}
    return ([f for f in group["folders"] if f.parent_id not in fids],
            [i for i in group["items"] if i.folder_id not in fids])


def _owner_ok(ctx: fc.Ctx, group: dict[str, list[Any]]) -> bool:
    """Darf diese Lehrkraft die Löschaktion rückgängig machen/endgültig löschen (wie beim Löschen selbst)?"""
    if ctx.manages_all:
        return True
    return all(ctx.may_edit(row.created_by) for row in (*group["items"], *group["folders"]))


def _need_right(ctx: fc.Ctx) -> None:
    if not has(ctx.user, "channels.trash"):
        raise HTTPException(403, "Dafür fehlt das Recht „Kursraum-Papierkorb nutzen“")
    if ctx.ch.archived:
        raise HTTPException(409, "Der Kursraum ist archiviert – Änderungen sind nicht mehr möglich")


@router.get("/channels/{channel_id}/trash")
def list_trash(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    days = retention_days()
    groups = _groups(db, ctx.ch.id)
    names = fc._user_names(db, [r.deleted_by for g in groups.values() for r in (*g["items"], *g["folders"])])
    sub_counts: dict[int, int] = {}
    item_ids = [i.id for g in groups.values() for i in g["items"]]
    for chunk in fc._chunks(item_ids):
        for iid, n in db.execute(select(AssignmentSubmission.item_id, func.count())
                                 .where(AssignmentSubmission.item_id.in_(chunk))
                                 .group_by(AssignmentSubmission.item_id)):
            sub_counts[iid] = int(n)
    can_use = has(user, "channels.trash") and not ctx.ch.archived
    entries = []
    for key, group in groups.items():
        root_folders, root_items = _roots(group)
        first = (root_folders or root_items or [None])[0]
        if first is None:
            continue
        when: datetime = max(r.deleted_at for r in (*group["items"], *group["folders"]))
        entries.append({
            "group": key,
            "kind": "folder" if root_folders else "item",
            "name": root_folders[0].name if root_folders else root_items[0].title,
            "type": None if root_folders else root_items[0].type,
            "type_label": "Ordner" if root_folders else fc.TYPE_LABELS.get(root_items[0].type, root_items[0].type),
            "folders": len(group["folders"]), "items": len(group["items"]),
            "submissions": sum(sub_counts.get(i.id, 0) for i in group["items"]),
            "deleted_at": iso(when), "deleted_by_name": names.get(first.deleted_by or 0, ""),
            "purge_at": iso(when + timedelta(days=days)),
            "can_restore": bool(can_use and _owner_ok(ctx, group)),
        })
    entries.sort(key=lambda e: e["deleted_at"] or "", reverse=True)
    return {"entries": entries, "retention_days": days, "can_use": can_use,
            "can_set_retention": has(user, "settings.edit")}


def _live_folder(db: Session, folder_id: int) -> bool:
    row = db.get(ChannelFolder, folder_id)           # der Identity-Map-Treffer kann ein gelöschter Ordner sein
    return row is not None and row.deleted_at is None


def _unique_name(db: Session, ctx: fc.Ctx, parent_id: Optional[int], name: str) -> str:
    cond = ChannelFolder.parent_id.is_(None) if parent_id is None else ChannelFolder.parent_id == parent_id
    taken = {n.casefold() for n in db.scalars(select(ChannelFolder.name).where(
        ChannelFolder.channel_id == ctx.ch.id, cond))}
    return fc._unique_folder_name(name, taken)


@router.post("/channels/{channel_id}/trash/{group}/restore")
def restore(channel_id: int, group: str, request: Request, user: AuthUser = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    _need_right(ctx)
    rows = _groups(db, ctx.ch.id).get(group)
    if rows is None:
        raise HTTPException(404, "Eintrag nicht im Papierkorb")
    if not _owner_ok(ctx, rows):
        raise HTTPException(403, fc.FOREIGN_MATERIAL)
    fc._check_item_capacity(db, ctx.ch.id, len(rows["items"]))
    root_folders, root_items = _roots(rows)
    for folder in root_folders:       # Elternordner weg oder selbst gelöscht → oben einsortieren
        if folder.parent_id is not None and not _live_folder(db, folder.parent_id):
            folder.parent_id = None
        folder.name = _unique_name(db, ctx, folder.parent_id, folder.name)
    for item in root_items:
        if item.folder_id is not None and not _live_folder(db, item.folder_id):
            item.folder_id = None
    for row in (*rows["items"], *rows["folders"]):
        row.deleted_at = row.deleted_by = row.trash_group = None
    audit(db, user, "channel_trash.restore", f"channel:{ctx.ch.id}",
          {"items": len(rows["items"]), "folders": len(rows["folders"])}, ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    return {"restored": group, "items": len(rows["items"]), "folders": len(rows["folders"])}


def purge_rows(db: Session, items: list[ChannelItem], folders: list[ChannelFolder]) -> int:
    """Endgültig löschen (ohne Commit): Material mit Abgaben/Dateien/Regeln, dazu alle noch im Papierkorb liegenden
    Unterelemente der Ordner; Ordner von unten nach oben. Rückgabe: Zahl der Material-Zeilen."""
    folder_ids = {f.id for f in folders}
    stack = list(folder_ids)
    while stack:                      # später separat gelöschte Unterordner/-material mitnehmen
        fid = stack.pop()
        for child in _trashed_folders(db, parent_id=fid):
            if child.id not in folder_ids:
                folder_ids.add(child.id)
                folders.append(child)
                stack.append(child.id)
    have = {i.id for i in items}
    for fid in folder_ids:
        for item in _trashed_items(db, folder_id=fid):
            if item.id not in have:
                have.add(item.id)
                items.append(item)
    for item in items:
        progress.forget_element(db, progress.ELEMENT_ITEM, item.id)
        assignment_tools.withdraw_from_gradebook(db, item.id)
    n = fc._delete_item_rows(db, items)
    by_id = {f.id: f for f in folders}
    for folder in sorted(folders, key=lambda f: fc._folder_depth(by_id, f.id), reverse=True):
        db.delete(folder)
        db.flush()
    return n


@router.delete("/channels/{channel_id}/trash/{group}")
def purge(channel_id: int, group: str, request: Request, user: AuthUser = Depends(current_user),
          db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    _need_right(ctx)
    rows = _groups(db, ctx.ch.id).get(group)
    if rows is None:
        raise HTTPException(404, "Eintrag nicht im Papierkorb")
    if not _owner_ok(ctx, rows):
        raise HTTPException(403, fc.FOREIGN_MATERIAL)
    n = purge_rows(db, rows["items"], rows["folders"])
    audit(db, user, "channel_trash.purge", f"channel:{ctx.ch.id}", {"items": n, "folders": len(rows["folders"])},
          ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    return {"purged": group, "items": n}


@router.delete("/channels/{channel_id}/trash")
def empty_trash(channel_id: int, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Papierkorb leeren – nur, was die Lehrkraft auch sonst löschen dürfte."""
    ctx = fc._ctx(db, user, channel_id, manage=True)
    _need_right(ctx)
    items = folders = skipped = 0
    for rows in _groups(db, ctx.ch.id).values():
        if not _owner_ok(ctx, rows):
            skipped += 1
            continue
        items += purge_rows(db, rows["items"], rows["folders"])
        folders += len(rows["folders"])
    audit(db, user, "channel_trash.empty", f"channel:{ctx.ch.id}", {"items": items, "folders": folders},
          ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    return {"items": items, "folders": folders, "skipped": skipped}


def run_purge(now: Optional[datetime] = None, days: Optional[int] = None) -> dict[str, int]:
    """Wartung: Abgelaufenes endgültig löschen (``trash_retention_days``). Rückgabe: ``{"channel_trash": Anzahl}``."""
    now = now or utcnow()
    cutoff = now - timedelta(days=days if days is not None else retention_days())
    total = 0
    with session_scope() as db:
        old_items = list(db.scalars(select(ChannelItem).where(ChannelItem.deleted_at < cutoff),
                                    execution_options=TRASHED))
        old_folders = list(db.scalars(select(ChannelFolder).where(ChannelFolder.deleted_at < cutoff),
                                      execution_options=TRASHED))
        if old_items or old_folders:
            total = purge_rows(db, old_items, old_folders) + len(old_folders)
    return {"channel_trash": total}
