"""Moodle-Kurssicherung (``.mbz``, gzip-TAR oder ZIP) → :class:`~.model.Bundle`.

Gelesen werden ``moodle_backup.xml`` (Info), ``course/course.xml``, ``users.xml``, ``roles.xml`` (Rollenzuweisungen),
``enrolments.xml``, ``groups.xml``, ``files.xml`` samt ``files/<xx>/<hash>`` (Dateien **mit Inhalt**) und alle Aufgaben
(``activities/assign_*/assign.xml``: Text-Abgaben, Bewertungen, Fälligkeit). Quizfragen, Notenbuch und Kompetenzen aus der
Sicherung sind nicht Teil dieses Lesers (siehe Matrix im Bericht) – dafür den Datenbankabzug nehmen.

Sicherheit: nichts wird auf die Platte entpackt (nur im Speicher gelesen), Mitgliederzahl/-größe sind begrenzt, XML mit
``DOCTYPE``/``ENTITY`` wird abgelehnt (keine Entity-Angriffe).
"""
from __future__ import annotations

import gzip
import io
import tarfile
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional

from .model import Bundle, FAssign, FCourse, FEnrol, FFile, FGroup, FPerson, FSubmission
from .text import clean, epoch_to_dt, epoch_to_iso, html_to_md

MAX_MEMBERS = 20000
MAX_MEMBER_BYTES = 60 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024


def _members(data: bytes) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    total = 0
    if data[:4] == b"PK\x03\x04":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if len(infos) > MAX_MEMBERS:
                raise ValueError("Zu viele Dateien in der Sicherung")
            for i in infos:
                if i.file_size > MAX_MEMBER_BYTES or ".." in i.filename.split("/"):
                    continue
                total += i.file_size
                if total > MAX_TOTAL_BYTES:
                    raise ValueError("Sicherung zu groß")
                out[i.filename] = zf.read(i)
        return out
    raw = gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tf:
        n = 0
        for m in tf:
            if not m.isfile():
                continue
            n += 1
            if n > MAX_MEMBERS:
                raise ValueError("Zu viele Dateien in der Sicherung")
            if m.size > MAX_MEMBER_BYTES or m.name.startswith("/") or ".." in m.name.split("/"):
                continue
            total += m.size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("Sicherung zu groß")
            fh = tf.extractfile(m)
            if fh is not None:
                out[m.name.lstrip("./")] = fh.read()
    return out


def _xml(files: dict[str, bytes], name: str, b: Bundle) -> Optional[ET.Element]:
    data = files.get(name)
    if data is None:
        return None
    head = data[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in data[:20000].upper():
        b.problem("format", name, "XML mit DOCTYPE/ENTITY wird aus Sicherheitsgründen abgelehnt")
        return None
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        b.problem("format", name, f"XML nicht lesbar: {exc}")
        return None


def _t(el: Optional[ET.Element], tag: str, default: str = "") -> str:
    if el is None:
        return default
    c = el.find(tag)
    return (c.text or default) if c is not None and c.text is not None else default


def read_moodle_mbz(data: bytes, *, name: str = "sicherung.mbz", instance: str = "standard") -> Bundle:
    b = Bundle(system="moodle-mbz", source=name.rsplit("/", 1)[-1], instance=instance)
    try:
        files = _members(data)
    except (OSError, EOFError, tarfile.TarError, zipfile.BadZipFile, ValueError) as exc:
        b.problem("format", name, f"Sicherung nicht lesbar: {exc}")
        return b
    if "moodle_backup.xml" not in files:
        b.problem("format", name, "moodle_backup.xml fehlt – keine Moodle-Sicherung")
        return b
    info = _xml(files, "moodle_backup.xml", b)
    if info is not None:
        b.version = _t(info.find("information"), "backup_release")
    cx = _xml(files, "course/course.xml", b)
    cid = (cx.get("id") if cx is not None else None) or "1"
    if cx is not None:
        b.courses[cid] = FCourse(cid, clean(_t(cx, "shortname")), clean(_t(cx, "fullname")), clean(_t(cx, "idnumber")),
                                 start=epoch_to_iso(_t(cx, "startdate")), end=epoch_to_iso(_t(cx, "enddate")),
                                 hidden=_t(cx, "visible", "1") == "0", summary=html_to_md(_t(cx, "summary")))
    else:
        b.problem("format", "course/course.xml", "Kursdaten fehlen")
        return b
    ux = _xml(files, "users.xml", b)
    for u in (ux.findall("user") if ux is not None else []):
        uid = u.get("id", "")
        b.persons[uid] = FPerson(uid, clean(_t(u, "firstname")), clean(_t(u, "lastname")), "student",
                                 email=clean(_t(u, "email")).lower(), username=clean(_t(u, "username")),
                                 ident=clean(_t(u, "idnumber")), class_hint=clean(_t(u, "department")))
    if ux is None:
        b.problem("format", "users.xml", "Sicherung ohne Benutzerdaten (Option „Benutzerdaten einbeziehen“ war aus)")
    role_short: dict[str, str] = {}
    rx = _xml(files, "roles.xml", b)
    teach: set[str] = set()
    if rx is not None:
        for r in rx.iter("role"):
            role_short[r.get("id", "")] = _t(r, "shortname")
        for a in rx.iter("assignment"):
            if role_short.get(_t(a, "roleid")) in ("editingteacher", "teacher"):
                teach.add(_t(a, "userid"))
    for uid in teach & set(b.persons):
        b.persons[uid].role = "teacher"
    ex = _xml(files, "enrolments.xml", b)
    for ue in (ex.iter("enrolment") if ex is not None else []):
        uid = _t(ue, "userid")
        if uid in b.persons:
            end = int(_t(ue, "timeend", "0") or 0)
            b.enrols.append(FEnrol(cid, uid, "teacher" if uid in teach else "student", _t(ue, "status", "0") == "0" and not end))
    gx = _xml(files, "groups.xml", b)
    for g in (gx.findall("group") if gx is not None else []):
        members = [_t(m, "userid") for m in g.iter() if m.tag.endswith("member") and m.find("userid") is not None]
        b.groups.append(FGroup(g.get("id", ""), cid, clean(_t(g, "name")), [m for m in members if m in b.persons]))
    # Dateien
    fx = _xml(files, "files.xml", b)
    for fe in (fx.findall("file") if fx is not None else []):
        fname = clean(_t(fe, "filename"))
        h = _t(fe, "contenthash")
        if fname in ("", ".") or not h:
            continue
        body = files.get(f"files/{h[:2]}/{h}")
        b.files.append(FFile(fe.get("id", h), fname, _t(fe, "mimetype"), int(_t(fe, "filesize", "0") or 0), cid,
                             f"{_t(fe, 'component')}/{_t(fe, 'filearea')}", _t(fe, "userid"), data=body))
    # Aufgaben
    for path in sorted(p for p in files if p.startswith("activities/assign_") and p.endswith("/assign.xml")):
        ax = _xml(files, path, b)
        a = ax.find("assign") if ax is not None else None
        if a is None:
            continue
        top = float(_t(a, "grade", "0") or 0)
        fa = FAssign(a.get("id", path), cid, clean(_t(a, "name")) or "Aufgabe", html_to_md(_t(a, "intro")),
                     epoch_to_dt(_t(a, "duedate")), epoch_to_dt(_t(a, "cutoffdate")), top if top > 0 else None,
                     team=_t(a, "teamsubmission", "0") == "1")
        grades = {_t(g, "userid"): g for g in a.iter("grade") if g.find("userid") is not None}
        for s in a.iter("submission"):
            uid = _t(s, "userid")
            if uid not in b.persons or _t(s, "latest", "1") != "1" or _t(s, "status") not in ("submitted",):
                continue
            ot = next((e for e in s.iter("submission_onlinetext")), None)
            sub = FSubmission(uid, "abgegeben", html_to_md(_t(ot, "onlinetext")) if ot is not None else "",
                              epoch_to_dt(_t(s, "timemodified")), int(_t(s, "attemptnumber", "0") or 0) + 1)
            g = grades.get(uid)
            val = float(_t(g, "grade", "-1") or -1) if g is not None else -1
            if val >= 0:
                sub.status, sub.points, sub.max_points = "bewertet", val, fa.max_points
                sub.graded_at = epoch_to_dt(_t(g, "timemodified"))
            fa.submissions.append(sub)
        b.assigns.append(fa)
    b.info["members"] = len(files)
    return b
