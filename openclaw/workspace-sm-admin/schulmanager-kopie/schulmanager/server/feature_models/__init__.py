"""SQLAlchemy-Modelle der Feature-Module (Erweiterung 2).

Jedes Feature legt hier ``<feature>.py`` mit Modellen auf ``schulmanager.server.db.Base`` an.
``load_all()`` importiert alle Module, damit Alembic und ``create_all`` sie kennen.
"""
from __future__ import annotations

import importlib
import pkgutil


def load_all() -> list[str]:
    names = []
    for mod in pkgutil.iter_modules(__path__):
        if not mod.name.startswith("_"):
            importlib.import_module(f"{__name__}.{mod.name}")
            names.append(mod.name)
    return names
