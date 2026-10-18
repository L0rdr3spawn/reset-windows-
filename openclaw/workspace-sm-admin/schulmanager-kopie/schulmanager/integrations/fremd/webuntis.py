"""WebUntis-JSON (JSON-RPC-Antworten, auch gesammelt als ``{"getTeachers": […]}``) → Bundle (Stammdaten).

Gelesen: ``getTeachers`` (Kürzel = ``name``), ``getStudents``, ``getKlassen``, ``getSubjects``, ``getRooms``. Die Art einer Datei
wird am Inhalt erkannt (Felder der ersten Einträge), nicht nur am Dateinamen. Der Stundenplan (``getTimetable``) wird
**nicht** übernommen – dafür Untis-GPU-Dateien verwenden (``/import/untis``). WebUntis liefert keine Klassenzugehörigkeit
der Schüler/innen; neue Schüler/innen brauchen daher eine Standardklasse beim Import.
"""
from __future__ import annotations

import json

from .._common import grade_from_name
from .model import Bundle, FPerson
from .text import clean

KINDS = {"getteachers": "teachers", "getstudents": "students", "getklassen": "classes", "getclasses": "classes",
         "getsubjects": "subjects", "getrooms": "rooms"}


def _kind(name: str, rows: list) -> str:
    stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    if stem in KINDS:
        return KINDS[stem]
    first = rows[0] if rows and isinstance(rows[0], dict) else {}
    if "key" in first and "foreName" in first:
        return "students"
    if "foreName" in first:
        return "teachers"
    if "teacher1" in first or ("longName" in first and "active" in first and "building" not in first and "alternateName" not in first):
        return "classes"
    if "building" in first:
        return "rooms"
    if "alternateName" in first:
        return "subjects"
    return ""


def read_webuntis(files: dict[str, bytes], *, instance: str = "standard") -> Bundle:
    b = Bundle(system="webuntis", source="WebUntis JSON", instance=instance)
    docs: list[tuple[str, list]] = []
    for name, data in sorted(files.items()):
        if not name.lower().endswith(".json"):
            continue
        try:
            doc = json.loads(data.decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError):
            b.problem("format", name, "Kein gültiges JSON")
            continue
        if isinstance(doc, dict) and "result" in doc:
            doc = doc["result"]
        if isinstance(doc, dict) and any(k.lower() in KINDS for k in doc):
            for k, v in doc.items():
                v = v.get("result", v) if isinstance(v, dict) else v
                if k.lower() in KINDS and isinstance(v, list):
                    docs.append((k, v))
        elif isinstance(doc, list):
            docs.append((name, doc))
        else:
            b.problem("format", name, "Unbekannte JSON-Struktur")
    for name, rows in docs:
        kind = _kind(name, rows)
        if not kind:
            b.problem("format", name, "Art der Liste nicht erkannt")
            continue
        for i, r in enumerate(rows):
            if not isinstance(r, dict) or r.get("id") is None:
                b.problem("zeile", f"{name}[{i}]", "Eintrag ohne id")
                continue
            if r.get("active") is False:
                continue
            if kind == "teachers":
                b.persons[f"T{r['id']}"] = FPerson(f"T{r['id']}", clean(r.get("foreName", "")), clean(r.get("longName", "")),
                                                   "teacher", ident=clean(r.get("name", "")))
            elif kind == "students":
                b.persons[f"S{r['id']}"] = FPerson(f"S{r['id']}", clean(r.get("foreName", "")), clean(r.get("longName", "")),
                                                   "student", username=clean(r.get("name", "")),
                                                   extra={"key": r.get("key")})
            elif kind == "classes":
                cid = clean(r.get("name", ""))
                grade = grade_from_name(cid)
                if cid and grade is not None:
                    b.classes.append({"id": cid, "name": clean(r.get("longName", "")) or cid, "grade": grade})
                else:
                    b.problem("zeile", f"{name}[{i}]", f"Klasse {cid!r}: Jahrgang nicht erkennbar")
            elif kind == "subjects":
                b.subjects.append({"id": clean(r.get("name", "")), "name": clean(r.get("longName", "")) or clean(r.get("name", ""))})
            elif kind == "rooms":
                b.rooms.append({"id": clean(r.get("name", "")), "name": clean(r.get("longName", "")) or clean(r.get("name", ""))})
    for p in b.persons.values():
        if not (p.first or p.last):
            b.problem("zeile", p.src_id, "Name fehlt")
    return b
