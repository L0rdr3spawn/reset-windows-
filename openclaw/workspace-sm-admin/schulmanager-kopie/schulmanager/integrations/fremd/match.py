"""Zuordnung von Personen aus einem Fremdsystem zu Schüler/innen und Lehrkräften des Planungsdokuments.

Reihenfolge (die erste eindeutige Stufe gewinnt):

1. ``linked``  – frühere Zuordnung aus einem Import (``import_links``), Ziel existiert noch
2. ``id``      – Kennung der Quelle (Moodle ``idnumber``, OneRoster ``identifier``) = Schüler-ID bzw. Lehrerkürzel
3. ``email``   – E-Mail-Adresse (Lehrkraft-Stammdaten oder Konto), Groß-/Kleinschreibung egal
4. ``name+geburtsdatum`` / ``name+klasse`` / ``name`` – Vor- und Nachname (Umlaute, ß, Bindestrich, Leerzeichen
   werden angeglichen); bei mehreren Treffern entscheiden Geburtsdatum, dann Klasse
5. ``ähnlich`` – Mehrfachnamen/vertauschte Reihenfolge; nur mit übereinstimmendem Geburtsdatum automatisch,
   sonst ``unsure`` (muss bestätigt werden)

Nicht zugeordnet wird, wenn der Name passt, aber beide Seiten ein **anderes** Geburtsdatum haben (``conflict``):
Namensvettern werden so nie zusammengelegt. Mehrere gleichwertige Treffer → ``ambiguous`` (Konfliktbericht, Auswahl
über ``person_map``).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .model import FPerson
from .text import fold


@dataclass
class Target:
    kind: str                 # student | teacher
    id: str
    name: str = ""
    class_id: str = ""
    birth: str = ""
    email: str = ""


@dataclass
class Match:
    person: str
    status: str = "unmatched"     # linked | matched | ambiguous | unsure | conflict | unmatched
    kind: str = ""
    target: str = ""
    via: str = ""
    candidates: list[str] = field(default_factory=list)
    note: str = ""


def _strong(name: str) -> str:
    return fold(name)


def _loose_keys(name: str) -> set[str]:
    words = [w for w in name.replace("-", " ").split() if w]
    keys: set[str] = set()
    if len(words) >= 2:
        keys.add(fold(words[0]) + fold(words[-1]))
        for k in range(1, len(words)):
            keys.add(fold("".join(words[k:])) + fold("".join(words[:k])))
    return {k for k in keys if k}


def person_keys(p: FPerson) -> tuple[str, set[str]]:
    strong = fold(p.first) + fold(p.last)
    loose: set[str] = set()
    fw = [w for w in p.first.replace("-", " ").split() if w]
    lw = [w for w in p.last.replace("-", " ").split() if w]
    if fw and lw:
        loose.add(fold(fw[0]) + fold(lw[-1]))
        loose.add(fold(fw[0]) + fold(p.last))
        loose.add(fold(p.first) + fold(lw[-1]))
    loose.add(fold(p.last) + fold(p.first))                # vertauscht
    loose.discard(strong)
    return strong, {k for k in loose if k}


class Index:
    def __init__(self, targets: Iterable[Target]):
        self.by_id: dict[str, Target] = {}
        self.by_email: dict[str, list[Target]] = {}
        self.strong: dict[str, list[Target]] = {}
        self.loose: dict[str, list[Target]] = {}
        self.items: dict[str, Target] = {}
        for t in targets:
            self.items[t.id] = t
            self.by_id.setdefault(fold(t.id), t)
            if t.email:
                self.by_email.setdefault(t.email.strip().lower(), []).append(t)
            self.strong.setdefault(_strong(t.name), []).append(t)
            for k in _loose_keys(t.name):
                self.loose.setdefault(k, []).append(t)


def _narrow(p: FPerson, cands: list[Target]) -> tuple[list[Target], str, str]:
    """Kandidaten über Geburtsdatum, dann Klasse eingrenzen → (Kandidaten, Weg, Hinweis)."""
    note = ""
    if p.birth:
        same = [c for c in cands if c.birth and c.birth == p.birth]
        differ = [c for c in cands if c.birth and c.birth != p.birth]
        unknown = [c for c in cands if not c.birth]
        if same:
            return same, "name+geburtsdatum", ""
        if differ and not unknown:
            return [], "", "Name gleich, Geburtsdatum abweichend"
        cands = unknown or cands
        note = ""
    if len(cands) > 1 and p.class_hint:
        by_class = [c for c in cands if c.class_id and fold(c.class_id) == fold(p.class_hint)]
        if by_class:
            return by_class, "name+klasse", note
    return cands, "name", note


def match_persons(persons: Iterable[FPerson], students: Iterable[Target], teachers: Iterable[Target],
                  accounts: Iterable[tuple[str, str, str]] = (), links: Optional[dict[str, tuple[str, str]]] = None,
                  overrides: Optional[dict[str, str]] = None) -> dict[str, Match]:
    """``accounts`` = ``(E-Mail, student_id, teacher_id)``; ``links`` = ``{Personen-src_id: (kind, target_id)}``;
    ``overrides`` = ``{Personen-src_id: Ziel-ID}`` (Entscheidung der Verwaltung, schlägt alles andere)."""
    sidx, tidx = Index(students), Index(teachers)
    acc_student: dict[str, str] = {}
    acc_teacher: dict[str, str] = {}
    for mail, sid, tid in accounts:
        if mail:
            if sid:
                acc_student.setdefault(mail.strip().lower(), sid)
            if tid:
                acc_teacher.setdefault(mail.strip().lower(), tid)
    links = links or {}
    overrides = overrides or {}
    out: dict[str, Match] = {}
    for p in persons:
        m = Match(p.src_id)
        out[p.src_id] = m
        if p.role not in ("student", "teacher"):
            m.status, m.note = "unmatched", "Rolle wird nicht zugeordnet"
            continue
        idx = sidx if p.role == "student" else tidx
        kind = p.role
        acc = acc_student if p.role == "student" else acc_teacher
        ov = overrides.get(p.src_id)
        if ov and ov in idx.items:
            m.status, m.kind, m.target, m.via = "matched", kind, ov, "manuell"
            continue
        ln = links.get(p.src_id)
        if ln and ln[0] == kind and ln[1] in idx.items:
            m.status, m.kind, m.target, m.via = "linked", kind, ln[1], "früherer Import"
            continue
        if p.ident:
            t = idx.by_id.get(fold(p.ident))
            if t is not None:
                m.status, m.kind, m.target, m.via = "matched", kind, t.id, "id"
                continue
        if p.email:
            key = p.email.strip().lower()
            tid = acc.get(key)
            cand = [idx.items[tid]] if tid in idx.items else idx.by_email.get(key, [])
            if len(cand) == 1:
                m.status, m.kind, m.target, m.via = "matched", kind, cand[0].id, "email"
                continue
            if len(cand) > 1:
                m.status, m.candidates, m.via = "ambiguous", [c.id for c in cand], "email"
                m.kind = kind
                continue
        strong, loose = person_keys(p)
        cands = list(idx.strong.get(strong, []))
        if cands:
            cands, via, note = _narrow(p, cands)
            if not cands:
                m.status, m.note, m.kind = "conflict", note, kind
                m.candidates = [c.id for c in idx.strong.get(strong, [])]
                continue
            if len(cands) == 1:
                m.status, m.kind, m.target, m.via, m.note = "matched", kind, cands[0].id, via, note
                continue
            m.status, m.kind, m.candidates, m.via = "ambiguous", kind, [c.id for c in cands], via
            continue
        lc: dict[str, Target] = {}
        for k in loose:
            for t in idx.loose.get(k, []):
                lc[t.id] = t
        if lc:
            cands, via, note = _narrow(p, list(lc.values()))
            if len(cands) == 1 and via == "name+geburtsdatum":
                m.status, m.kind, m.target, m.via = "matched", kind, cands[0].id, "ähnlich+geburtsdatum"
            elif cands:
                m.status, m.kind, m.candidates, m.via = "unsure", kind, [c.id for c in cands], "ähnlich"
                m.note = "ähnlicher Name – bitte bestätigen"
            continue
        m.kind = kind
    return out
