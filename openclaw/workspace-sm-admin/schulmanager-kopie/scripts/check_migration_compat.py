#!/usr/bin/env python3
"""Prüft Alembic-Migrationen auf Abwärtskompatibilität (Expand/Contract) für den rollenden Betrieb mit mehreren Servern.

Beim rollenden Update läuft kurzzeitig der **alte** Code auf dem **neuen** Schema. Erlaubt („expand“) sind deshalb nur:
neue Tabellen, neue Spalten, die NULL erlauben oder einen ``server_default`` haben, neue Indizes, Datenfüllung.
Nicht abwärtskompatibel („contract“): Spalte/Tabelle löschen, umbenennen, Typ ändern, Spalte auf NOT NULL setzen,
neue NOT-NULL-Spalte ohne ``server_default``, Löschen einer Einschränkung, die der alte Code noch voraussetzt.

    python scripts/check_migration_compat.py [Revision …]     # ohne Angabe: alle; Ausgabe: Befund je Migration

Release-Regel: Enthält ein Release eine Migration mit Befund, wird es mit ``--breaking`` angelegt
(``python -m lizenzserver.updates_cli release-add … --breaking``). Schulen mit mehreren Servern wechseln dann automatisch in
ein gemeinsames Wartungsfenster. Besser: in zwei Releases aufteilen (erst „expand“, im nächsten „contract“).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

VERSIONS = Path(__file__).resolve().parent.parent / "schulmanager" / "server" / "migrations" / "versions"

#: Wird als **nicht** abwärtskompatibel gemeldet, sobald es in ``upgrade()`` vorkommt.
BREAKING_CALLS = {"drop_column": "Spalte löschen", "drop_table": "Tabelle löschen", "rename_table": "Tabelle umbenennen",
                  "drop_constraint": "Einschränkung löschen"}


def _name(call: ast.Call) -> str:
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def _kw(call: ast.Call, key: str):
    for k in call.keywords:
        if k.arg == key:
            return k.value
    return None


def _column_call(node: ast.AST) -> ast.Call | None:
    """Das ``sa.Column(...)`` hinter ``op.add_column(tabelle, sa.Column(...))``."""
    if isinstance(node, ast.Call) and _name(node) == "Column":
        return node
    return None


def findings(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for fn in tree.body:
        if not (isinstance(fn, ast.FunctionDef) and fn.name == "upgrade"):
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            name = _name(node)
            if name in BREAKING_CALLS:
                out.append(f"Zeile {node.lineno}: {BREAKING_CALLS[name]} ({name})")
            elif name == "alter_column":
                if _kw(node, "new_column_name") is not None:
                    out.append(f"Zeile {node.lineno}: Spalte umbenennen")
                elif _kw(node, "type_") is not None:
                    out.append(f"Zeile {node.lineno}: Spaltentyp ändern")
                else:
                    nullable = _kw(node, "nullable")
                    if isinstance(nullable, ast.Constant) and nullable.value is False:
                        out.append(f"Zeile {node.lineno}: Spalte auf NOT NULL setzen")
            elif name == "add_column":
                col = next((c for c in map(_column_call, node.args) if c is not None), None)
                if col is not None:
                    nullable = _kw(col, "nullable")
                    not_null = isinstance(nullable, ast.Constant) and nullable.value is False
                    if not_null and _kw(col, "server_default") is None:
                        out.append(f"Zeile {node.lineno}: neue NOT-NULL-Spalte ohne server_default")
    return out


def main(argv: list[str]) -> int:
    files = sorted(VERSIONS.glob("*.py"))
    if argv:
        files = [f for f in files if any(f.name.startswith(a) for a in argv)]
    bad = 0
    for f in files:
        res = findings(f)
        if res:
            bad += 1
            print(f"{f.name}:")
            for r in res:
                print(f"   - {r}")
    print(f"{bad} von {len(files)} Migrationen mit Befund.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
