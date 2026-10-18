"""Tabelle ``stored_files`` – Metadaten verschlüsselt abgelegter Dateien (Agent Basis, ARCHITECTURE.md §9.2).

Die Inhalte liegen verschlüsselt unter ``config.files_dir`` (Standard ``<SM_DATA_DIR>/files/xx/yy/<id>``), siehe
``server/files.py``. Auch der Dateiname ist verschlüsselt (Spalte ``filename`` enthält ein ``SM1.``-Token,
AAD ``stored_files.filename:<id>``); im Code liest man ihn über die Eigenschaft :attr:`StoredFile.filename`.
Zeilen bitte nur über ``files.store_bytes``/``files.store_upload`` anlegen.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from schulmanager.server.db import Base, utcnow


class StoredFile(Base):
    """Eine hochgeladene Datei (Inhalt verschlüsselt auf der Platte)."""
    __tablename__ = "stored_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)                 # UUID (str)
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    filename_token: Mapped[str] = mapped_column("filename", Text)                # verschlüsselt (SM1.-Token)
    content_type: Mapped[str] = mapped_column(String(150))                       # aus dem Inhalt erkannt
    kind: Mapped[str] = mapped_column(String(20))                                # pdf|png|docx|… (files.KINDS)
    size: Mapped[int] = mapped_column(BigInteger)                                # Klartext-Bytes
    sha256: Mapped[str] = mapped_column(String(64))                              # des Klartexts (hex)
    purpose: Mapped[str] = mapped_column(String(40))                             # z. B. channel_material
    ref_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)   # angehängt an … (Access-Check)
    ref_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    key_id: Mapped[str] = mapped_column(String(32))                              # Master-Schlüssel des Blobs
    scan_status: Mapped[str] = mapped_column(String(20), default="unscanned")    # clean|unscanned|error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # letztes attach/detach
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # ------------------------------------------------------------------ Dateiname (verschlüsselt)
    @property
    def filename_aad(self) -> str:
        return f"stored_files.filename:{self.id}"

    @property
    def filename(self) -> str:
        """Dateiname im Klartext (entschlüsselt bei jedem Zugriff)."""
        from schulmanager.server import crypto

        if not self.filename_token:
            return ""
        return crypto.decrypt_text(self.filename_token, self.filename_aad)

    @filename.setter
    def filename(self, value: str) -> None:
        from schulmanager.server import crypto

        if not self.id:
            raise ValueError("StoredFile.id muss vor dem Dateinamen gesetzt sein (AAD)")
        self.filename_token = crypto.encrypt_text(value, self.filename_aad)

    @property
    def attached(self) -> bool:
        return bool(self.ref_type)

    def __repr__(self) -> str:  # ohne Dateinamen (personenbezogen)
        return f"<StoredFile {self.id} {self.kind} {self.size}B ref={self.ref_type}:{self.ref_id}>"


Index("ix_stored_files_ref", StoredFile.ref_type, StoredFile.ref_id)
