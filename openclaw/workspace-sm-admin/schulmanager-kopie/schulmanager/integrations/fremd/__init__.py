"""Importe aus Fremdsystemen (Moodle, OneRoster, WebUntis, IServ, SchILD/ASV) – Leser auf ein neutrales Modell.

Reine Bibliothek ohne Datenbank (nur Standardbibliothek). Die Anwendung der Daten auf Planungsdokument und Datenbank
(Zuordnung, Trockenlauf, Idempotenz, Rückgängig, Audit) steht in ``schulmanager/server/import_fremd.py``.
Überblick und Matrix: ``docs/IMPORT-FREMDSYSTEME.md``.
"""
from .model import Bundle, Problem  # noqa: F401
