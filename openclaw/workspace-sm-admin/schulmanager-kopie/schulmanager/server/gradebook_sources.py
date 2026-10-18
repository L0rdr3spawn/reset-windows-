"""Notenbuch: Übernahme von Ergebnissen aus anderen Bereichen (Klausuren, Aufgaben, Selbsttests …).

Schnittstelle für andere Bereiche (Doku: ``docs/NOTENBUCH.md`` §6) – zwei Wege, beide liefern *Ergebnisse* mit
Elementtyp + ID + Punkte bzw. Note + Datum:

**Schieben** (Aufgaben M1, Selbsttests M3 …): nach dem Bewerten bzw. Abschluss aufrufen::

    from schulmanager.server import gradebook_sources as gs
    gs.publish_results(db, source_type="aufgabe", source_id=str(item.id), course_id=course_id, part=0,
                       title=item.title, date="2026-10-13", max_points=20,
                       results=[gs.SourceResult(student_id="S12", points=17.5), gs.SourceResult("S13", grade="2+")])
    db.commit()

* ``source_type``: kurzes Kennwort (``aufgabe``, ``selbsttest``, ``klausur`` …, max. 30 Zeichen); ``source_id``:
  stabile ID des Elements (max. 80 Zeichen). Beides zusammen kennzeichnet die Quelle eindeutig.
* Pro Person entweder ``points`` (mit ``max_points`` der Quelle) oder ``grade`` (Note als Text, in der Skala des
  Notenbuchs). Erneutes Aufrufen aktualisiert die Ergebnisse; bereits übernommene Leistungen im Notenbuch ziehen
  nach (Eintragungen, die die Lehrkraft von Hand geändert hat, bleiben).
* :func:`withdraw_results` nimmt eine Quelle zurück (z. B. Aufgabe gelöscht).
* Nichts wird automatisch ins Notenbuch geschrieben: die Lehrkraft sieht die Quelle unter „Übernehmen“ und entscheidet
  je Notenbuch, ob sie die Leistung übernimmt oder abwählt.

**Ziehen** (nur Bereiche mit eigener Tabelle, z. B. Klausuren): :func:`register_provider` mit einer Funktion
``fetch(db, school, course_id, part) -> list[SourceBundle]``. Die Klausurnoten (``exam_results``) sind so
angeschlossen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .db import utcnow
from .feature_models.gradebook import GradeBook, GradeEntry, GradeItem, GradeSourceLink, GradeSourceResult


@dataclass
class SourceResult:
    student_id: str
    points: Optional[float] = None
    grade: str = ""


@dataclass
class SourceBundle:
    """Eine Quelle mit ihren Ergebnissen (Kandidat zum Übernehmen)."""
    source_type: str
    source_id: str
    title: str
    date: str = ""
    max_points: Optional[float] = None
    results: dict[str, SourceResult] = field(default_factory=dict)


Provider = Callable[[Session, Any, str, int], list[SourceBundle]]
_providers: dict[str, tuple[str, Provider]] = {}
_LABELS: dict[str, str] = {"klausur": "Klausur/Test", "aufgabe": "Aufgabe", "selbsttest": "Selbsttest"}


def register_provider(source_type: str, label: str, fetch: Provider) -> None:
    _providers[source_type] = (label, fetch)


def source_labels() -> dict[str, str]:
    out = dict(_LABELS)
    out.update({t: lab for t, (lab, _) in _providers.items()})
    return out


def set_label(source_type: str, label: str) -> None:
    """Anzeigename einer geschobenen Quellenart (z. B. ``"Aufgabe"``)."""
    _LABELS[source_type] = label


# ------------------------------------------------------------------------------------------------ Schieben
def publish_results(db: Session, *, source_type: str, source_id: str, course_id: str, part: int = 0, title: str = "",
                    date: str = "", max_points: Optional[float] = None, results: Iterable[SourceResult]) -> int:
    """Ergebnisse einer Quelle ablegen bzw. aktualisieren und übernommene Leistungen nachziehen. Gibt die Zahl der
    Ergebnisse zurück. Commit macht der Aufrufer."""
    if not source_type or len(source_type) > 30 or not source_id or len(source_id) > 80:
        raise ValueError("source_type/source_id fehlen oder sind zu lang")
    existing = {r.student_id: r for r in db.scalars(select(GradeSourceResult).where(
        GradeSourceResult.source_type == source_type, GradeSourceResult.source_id == source_id))}
    seen: set[str] = set()
    n = 0
    for res in results:
        if res.points is None and not (res.grade or "").strip():
            continue
        row = existing.get(res.student_id)
        if row is None:
            row = GradeSourceResult(source_type=source_type, source_id=source_id, student_id=res.student_id)
            db.add(row)
        row.course_id, row.part, row.title, row.date = course_id, int(part), (title or "")[:120], (date or "")[:10]
        row.points, row.max_points = res.points, max_points
        row.grade = (res.grade or "").strip()[:20]
        row.updated_at = utcnow()
        seen.add(res.student_id)
        n += 1
    for sid, row in existing.items():            # Ergebnis nicht mehr geliefert (z. B. Bewertung zurückgenommen)
        if sid not in seen:
            db.delete(row)
    db.flush()
    sync_links(db, source_type, source_id)
    return n


def withdraw_results(db: Session, source_type: str, source_id: str) -> None:
    """Quelle zurücknehmen: Ergebnisse weg; übernommene Leistungen bleiben mit ihren Noten stehen."""
    db.execute(delete(GradeSourceResult).where(GradeSourceResult.source_type == source_type,
                                               GradeSourceResult.source_id == source_id))


# ------------------------------------------------------------------------------------------------ Ziehen
def _exam_provider(db: Session, school, course_id: str, part: int) -> list[SourceBundle]:
    from .feature_models.grades import ExamResult
    from .gradebook_store import dec
    out = []
    for e in school.exams:
        if e.course_id != course_id or (e.part is not None and e.part != part):
            continue
        rows = list(db.scalars(select(ExamResult).where(ExamResult.exam_id == e.id)))
        results = {}
        for r in rows:
            grade = dec(r.grade_enc, r.aad("grade")).strip()
            if grade:
                results[r.student_id] = SourceResult(r.student_id, None, grade)
        if results:
            out.append(SourceBundle("klausur", e.id, e.title or ("Test" if getattr(e, "kind", "") == "test"
                                                                  else "Klausur"), e.date, None, results))
    return out


register_provider("klausur", "Klausur/Test", _exam_provider)


def fetch_bundles(db: Session, school, course_id: str, part: int) -> list[SourceBundle]:
    """Alle Quellen, die für diesen Kursteil Ergebnisse haben (Ziehen + Schieben)."""
    out: list[SourceBundle] = []
    for _, (_, fn) in _providers.items():
        try:
            out.extend(fn(db, school, course_id, part))
        except Exception:  # noqa: BLE001 - eine defekte Quelle darf das Notenbuch nicht blockieren
            continue
    pushed: dict[tuple[str, str], SourceBundle] = {}
    for r in db.scalars(select(GradeSourceResult).where(GradeSourceResult.course_id == course_id,
                                                        GradeSourceResult.part == part)
                        .order_by(GradeSourceResult.source_type, GradeSourceResult.source_id)):
        b = pushed.setdefault((r.source_type, r.source_id),
                              SourceBundle(r.source_type, r.source_id, r.title, r.date, r.max_points))
        b.results[r.student_id] = SourceResult(r.student_id, r.points, r.grade)
    out.extend(pushed.values())
    return out


def find_bundle(db: Session, school, course_id: str, part: int, source_type: str, source_id: str
                ) -> Optional[SourceBundle]:
    for b in fetch_bundles(db, school, course_id, part):
        if b.source_type == source_type and b.source_id == source_id:
            return b
    return None


# --------------------------------------------------------------------------------------------- Übernehmen
def entry_value(bundle: SourceBundle, res: SourceResult) -> str:
    if bundle.max_points and res.points is not None:
        return format(round(res.points, 4), "g")
    return res.grade


def apply_bundle(db: Session, user, book: GradeBook, item: GradeItem, bundle: SourceBundle,
                 students: Iterable[str]) -> int:
    """Ergebnisse in die Leistung schreiben (neue Eintragungen; vorhandene nur, wenn sie noch aus der Quelle
    stammen). Gibt die Zahl der geänderten Eintragungen zurück."""
    from . import crypto
    from .gradebook_store import dec, log
    changed = 0
    existing = {e.student_id: e for e in db.scalars(select(GradeEntry).where(GradeEntry.item_id == item.id))}
    name = (getattr(user, "display_name", "") or getattr(user, "username", "") or "Übernahme")[:200]
    for sid in students:
        res = bundle.results.get(sid)
        if res is None:
            continue
        value = entry_value(bundle, res)
        if not value:
            continue
        row = existing.get(sid)
        if row is None:
            row = GradeEntry(item_id=item.id, student_id=sid, value_enc="", note_enc="", status="", makeup_date="",
                             from_source=True, entered_by=getattr(user, "id", None) or None, entered_by_name=name,
                             entered_at=utcnow())
            db.add(row)
            db.flush()
            old = ""
        elif row.from_source:
            old = dec(row.value_enc, row.aad("value"))
            if old == value:
                continue
        else:
            continue
        row.value_enc = crypto.encrypt_text(value, row.aad("value"))
        row.entered_at = utcnow()
        log(db, user, book.id, "entry", item_id=item.id, student_id=sid,
            detail={"from": old, "to": value, "source": bundle.source_type})
        changed += 1
    return changed


def sync_links(db: Session, source_type: str, source_id: str) -> int:
    """Alle übernommenen Leistungen dieser Quelle auffrischen (gesperrte Notenbücher bleiben unberührt)."""
    from .store import get_store
    school = get_store().school
    total = 0
    links = list(db.scalars(select(GradeSourceLink).where(
        GradeSourceLink.source_type == source_type, GradeSourceLink.source_id == source_id,
        GradeSourceLink.state == "adopted")))
    for link in links:
        book = db.get(GradeBook, link.book_id)
        item = db.get(GradeItem, link.item_id) if link.item_id else None
        if book is None or item is None or book.locked_at is not None:
            continue
        bundle = find_bundle(db, school, book.course_id, book.part, source_type, source_id)
        if bundle is None:
            continue
        from .gradebook_store import roster
        total += apply_bundle(db, None, book, item, bundle, roster(school, book.course_id, book.part))
    return total
