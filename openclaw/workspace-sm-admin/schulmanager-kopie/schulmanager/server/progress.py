"""Lernfortschritt im Kursraum: Abschlussverfolgung und bedingte Freigabe (Moodle-Lücken M2, ``docs/LERNFORTSCHRITT.md``).

Reine Logik + Datenzugriff, **ohne** Routen (damit ``features_channels`` sie ohne Import-Schleife nutzen kann).

Elemente
--------
Ein *Element* ist alles, was abgeschlossen oder gesperrt werden kann – adressiert generisch über
``(element_type, element_id)``. Eingebaut ist ``item`` (Material/Aufgabe des Kursraums, :class:`ItemProvider`). Neue
Elementarten (Abstimmung, Selbsttest, Gruppenaufgabe …) melden sich mit :func:`register_provider` an:

* ``type`` / ``label`` – Schlüssel und Anzeigename (z. B. ``"poll"``, ``"Abstimmung"``)
* ``modes`` – erlaubte Abschlussbedingungen (Teilmenge von :data:`MODES`)
* ``elements(db, channel_id) -> list[Element]`` – alle Elemente des Kursraums (ohne Gelöschte)
* ``facts(db, channel_id, user_ids, ids) -> {(user_id, element_id): Facts}`` – was die Konten mit dem Element getan haben
  (``viewed``/``submitted``/``graded``/``score_percent``/``note``)
* optional ``created_by(db, element_id) -> int | None`` für die Rechteprüfung (Ersteller; sonst jede Lehrkraft des Raums)

Gruppen (Kursgruppen, Agent M1) hängen sich mit :func:`register_group_provider` an: ``list_groups(db, channel_id)``
liefert ``[{"id": int, "name": str}]``, ``member_ids(db, channel_id, group_id)`` die Konten der Gruppe. Ohne Anbieter
ist die Bedingung „Gruppe“ nicht wählbar.

Bedingte Freigabe
-----------------
``availability_rules.tree`` ist ein Baum ``{"op": "and"|"or", "items": [Knoten|Blatt, …]}`` (Tiefe ≤ 3, ≤ 20 Blätter).
Blätter: ``completed`` (anderes Element erledigt), ``score`` (Punkte ≥ ``min_percent``), ``note`` (Note ≤
``max_note``), ``group``, ``date`` (``from``/``until``, naive UTC) und ``release`` (die eigene Zeitfreigabe des
Elements – geplant bzw. „zur Stunde“ – ist erreicht). Ohne ``release``-Blatt gilt die Zeitfreigabe zusätzlich (UND);
mit ``release`` ist sie Teil der Verknüpfung (z. B. „zur Stunde ODER Aufgabe A erledigt“). „Verborgen“ (Material oder
Ordner) sperrt immer hart.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Optional, Protocol, Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from schulmanager import channels as logic

from .feature_models.channels import AssignmentSubmission, ChannelItem, ChannelItemView
from .feature_models.progress import AvailabilityRule, CompletionMark, CompletionRule

log = logging.getLogger("schulmanager.progress")

ELEMENT_ITEM = "item"
MODES = ("manual", "viewed", "submitted", "graded", "passed")
MODE_LABELS = {"manual": "Selbst abhaken", "viewed": "Angesehen", "submitted": "Abgegeben",
               "graded": "Bewertet", "passed": "Bestanden"}
DEFAULT_PASS_PERCENT = 50
PASS_NOTE = 4.0                       # ohne Prozentwert: Note 4,0 oder besser gilt als bestanden
MAX_DEPTH = 3
MAX_LEAVES = 20
LEAF_TYPES = ("completed", "score", "note", "group", "date", "release")
TZ = ZoneInfo("Europe/Berlin")
_CHUNK = 500


# =========================================================================== Anbieter
@dataclass(frozen=True)
class Element:
    type: str
    id: int
    title: str
    kind_label: str = ""
    modes: tuple[str, ...] = ("manual",)
    folder_id: Optional[int] = None


@dataclass
class Facts:
    """Was ein Konto mit einem Element getan hat (Grundlage der automatischen Abschlussbedingungen)."""
    viewed: bool = False
    submitted: bool = False
    graded: bool = False
    score_percent: Optional[float] = None
    note: Optional[float] = None


class ElementProvider(Protocol):  # pragma: no cover - Schnittstelle
    type: str
    label: str
    modes: tuple[str, ...]

    def elements(self, db: Session, channel_id: int) -> list[Element]: ...

    def facts(self, db: Session, channel_id: int, user_ids: Sequence[int], ids: Sequence[int]
              ) -> dict[tuple[int, int], Facts]: ...


class GroupProvider(Protocol):  # pragma: no cover - Schnittstelle
    def list_groups(self, db: Session, channel_id: int) -> list[dict[str, Any]]: ...

    def member_ids(self, db: Session, channel_id: int, group_id: int) -> set[int]: ...


_providers: dict[str, Any] = {}
_group_provider: Optional[Any] = None


def register_provider(provider: Any) -> None:
    """Neue Elementart anmelden (siehe Modul-Doku). Eine erneute Anmeldung ersetzt die alte."""
    bad = [m for m in provider.modes if m not in MODES]
    if bad:
        raise ValueError(f"Unbekannte Abschlussbedingung(en): {bad}")
    _providers[provider.type] = provider


def register_group_provider(provider: Any) -> None:
    global _group_provider
    _group_provider = provider


def providers() -> dict[str, Any]:
    return dict(_providers)


def group_provider() -> Optional[Any]:
    return _group_provider


def _chunks(values: Iterable[Any], size: int = _CHUNK):
    seq = list(values)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# =========================================================================== Noten/Punkte aus Freitext
_PCT = re.compile(r"^(\d+(?:[.,]\d+)?)\s*%$")
_FRACTION = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:/|von)\s*(\d+(?:[.,]\d+)?)(?:\s*(?:punkte|pkt\.?|p\.?))?$", re.I)
_NOTE = re.compile(r"^([1-6])\s*([+-])?$")
_NOTE_DEC = re.compile(r"^([1-6])[.,](\d)$")
_NOTE_RANGE = re.compile(r"^([1-6])\s*[-–]\s*([1-6])$")


def _num(text: str) -> float:
    return float(text.replace(",", "."))


def parse_grade(text: str) -> tuple[Optional[float], Optional[float]]:
    """``(Prozent, Note)`` aus dem Bewertungstext („80 %“, „12/15“, „2+“, „2,5“, „2-3“); unbekannt = ``None``.

    Bloße Punktzahlen ohne Maximum („12 Punkte“) sind nicht auswertbar."""
    t = (text or "").strip()
    if not t:
        return None, None
    m = _PCT.match(t)
    if m:
        return min(_num(m.group(1)), 100.0), None
    m = _FRACTION.match(t)
    if m:
        top = _num(m.group(2))
        return (min(_num(m.group(1)) / top * 100.0, 100.0) if top > 0 else None), None
    m = _NOTE.match(t)
    if m:
        base = float(m.group(1))
        shift = {"+": -0.3, "-": 0.3}.get(m.group(2) or "", 0.0)
        return None, round(min(max(base + shift, 1.0), 6.0), 1)
    m = _NOTE_DEC.match(t)
    if m:
        return None, float(f"{m.group(1)}.{m.group(2)}")
    m = _NOTE_RANGE.match(t)
    if m:
        return None, (float(m.group(1)) + float(m.group(2))) / 2
    return None, None


def passes(facts: Facts, pass_percent: Optional[int]) -> bool:
    """Bestanden: Prozent ≥ Grenze, sonst Note 4,0 oder besser; ohne auswertbares Ergebnis nicht."""
    if facts.score_percent is not None:
        return facts.score_percent + 1e-9 >= (pass_percent if pass_percent is not None else DEFAULT_PASS_PERCENT)
    if facts.note is not None:
        return facts.note <= PASS_NOTE + 1e-9
    return False


# =========================================================================== Eingebauter Anbieter: Material/Aufgaben
class ItemProvider:
    type = ELEMENT_ITEM
    label = "Material und Aufgaben"
    modes = MODES

    @staticmethod
    def _modes(item: ChannelItem) -> tuple[str, ...]:
        if item.type == "assignment" or item.submittable:
            return MODES
        return ("manual", "viewed")

    def elements(self, db: Session, channel_id: int) -> list[Element]:
        out = []
        for item in db.scalars(select(ChannelItem).where(ChannelItem.channel_id == channel_id,
                                                         ChannelItem.info_card.is_(False))
                               .order_by(ChannelItem.position, ChannelItem.id)):
            out.append(Element(ELEMENT_ITEM, item.id, item.title, {"file": "Datei", "link": "Link",
                                                                   "text": "Textseite", "assignment": "Aufgabe"}
                               .get(item.type, item.type), self._modes(item), item.folder_id))
        return out

    def facts(self, db: Session, channel_id: int, user_ids: Sequence[int], ids: Sequence[int]
              ) -> dict[tuple[int, int], Facts]:
        out: dict[tuple[int, int], Facts] = {}
        uids = [u for u in user_ids if u]
        if not uids or not ids:
            return out
        for id_chunk in _chunks(ids):
            for iid, uid in db.execute(select(ChannelItemView.item_id, ChannelItemView.user_id)
                                       .where(ChannelItemView.item_id.in_(id_chunk),
                                              ChannelItemView.user_id.in_(uids))):
                out.setdefault((uid, iid), Facts()).viewed = True
            for sub in db.scalars(select(AssignmentSubmission)
                                  .where(AssignmentSubmission.item_id.in_(id_chunk),
                                         AssignmentSubmission.student_user_id.in_(uids))):
                if sub.submitted_at is None:
                    continue
                f = out.setdefault((sub.student_user_id, sub.item_id), Facts())
                f.submitted = True
                if sub.status == "bewertet":
                    f.graded = True
                    f.score_percent, f.note = parse_grade(sub.read_text("grade"))
                    points, maximum = getattr(sub, "points", None), getattr(sub, "max_points", None)
                    if points is not None and maximum:        # Punkte aus dem Bewertungsraster (Aufgaben-Erweiterung)
                        f.score_percent = min(max(points / maximum * 100.0, 0.0), 100.0)
        return out

    def created_by(self, db: Session, element_id: int) -> Optional[int]:
        item = db.get(ChannelItem, element_id)
        return item.created_by if item else None


register_provider(ItemProvider())


# =========================================================================== Bedingungsbaum
class TreeError(ValueError):
    """Ungültige Bedingung (Text für den Anwender)."""


def _parse_dt(value: Any, what: str) -> Optional[str]:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise TreeError(f"{what}: ungültiges Datum") from exc
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat(timespec="seconds")


def _walk_leaves(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for sub in node.get("items", []):
        if sub.get("type"):
            yield sub
        else:
            yield from _walk_leaves(sub)


def tree_refs(tree: Optional[dict[str, Any]]) -> set[tuple[str, int]]:
    """Elemente, auf die sich ein Baum bezieht."""
    if not tree:
        return set()
    return {(leaf["element_type"], int(leaf["element_id"])) for leaf in _walk_leaves(tree)
            if leaf["type"] in ("completed", "score", "note")}


def has_release(tree: Optional[dict[str, Any]]) -> bool:
    return bool(tree) and any(leaf["type"] == "release" for leaf in _walk_leaves(tree))


def normalize_tree(raw: Any, *, valid_ref: Callable[[str, int, str], Optional[str]],
                   group_ok: Callable[[int], bool]) -> Optional[dict[str, Any]]:
    """Prüft und bereinigt einen Bedingungsbaum. ``None`` = keine Bedingung.

    ``valid_ref(element_type, element_id, leaf_type)`` liefert einen Fehlertext oder ``None``."""
    if raw in (None, {}, []):
        return None
    if not isinstance(raw, dict):
        raise TreeError("Die Bedingungen sind ungültig")
    leaves = [0]

    def node(n: Any, depth: int) -> dict[str, Any]:
        if depth > MAX_DEPTH:
            raise TreeError(f"Bedingungen lassen sich höchstens {MAX_DEPTH} Ebenen tief verschachteln")
        if not isinstance(n, dict) or n.get("op") not in ("and", "or") or not isinstance(n.get("items"), list):
            raise TreeError("Die Bedingungen sind ungültig")
        items = []
        for sub in n["items"]:
            if isinstance(sub, dict) and "type" in sub:
                leaves[0] += 1
                if leaves[0] > MAX_LEAVES:
                    raise TreeError(f"Höchstens {MAX_LEAVES} Bedingungen je Element")
                items.append(leaf(sub))
            else:
                inner = node(sub, depth + 1)
                if inner["items"]:
                    items.append(inner)
        return {"op": n["op"], "items": items}

    def leaf(spec: dict[str, Any]) -> dict[str, Any]:
        kind = spec.get("type")
        if kind not in LEAF_TYPES:
            raise TreeError("Unbekannte Bedingung")
        if kind in ("completed", "score", "note"):
            try:
                etype, eid = str(spec.get("element_type") or ""), int(spec.get("element_id"))
            except (TypeError, ValueError) as exc:
                raise TreeError("Bitte ein Element wählen") from exc
            err = valid_ref(etype, eid, kind)
            if err:
                raise TreeError(err)
            out: dict[str, Any] = {"type": kind, "element_type": etype, "element_id": eid}
            if kind == "score":
                try:
                    pct = float(spec.get("min_percent"))
                except (TypeError, ValueError) as exc:
                    raise TreeError("Bitte die Mindestpunktzahl in Prozent angeben") from exc
                if not 0 <= pct <= 100:
                    raise TreeError("Die Mindestpunktzahl liegt zwischen 0 und 100 Prozent")
                out["min_percent"] = round(pct, 1)
            if kind == "note":
                try:
                    note = float(spec.get("max_note"))
                except (TypeError, ValueError) as exc:
                    raise TreeError("Bitte die schlechteste erlaubte Note angeben") from exc
                if not 1 <= note <= 6:
                    raise TreeError("Noten liegen zwischen 1 und 6")
                out["max_note"] = round(note, 1)
            return out
        if kind == "group":
            try:
                gid = int(spec.get("group_id"))
            except (TypeError, ValueError) as exc:
                raise TreeError("Bitte eine Gruppe wählen") from exc
            if not group_ok(gid):
                raise TreeError("Diese Gruppe gibt es in diesem Kursraum nicht")
            return {"type": "group", "group_id": gid}
        if kind == "date":
            start, end = _parse_dt(spec.get("from"), "Ab"), _parse_dt(spec.get("until"), "Bis")
            if start is None and end is None:
                raise TreeError("Bitte ein Datum angeben")
            if start and end and end <= start:
                raise TreeError("„Bis“ muss nach „Ab“ liegen")
            return {"type": "date", "from": start, "until": end}
        return {"type": "release"}

    tree = node(raw, 1)
    return tree if tree["items"] else None


def _fmt_dt(value: str) -> str:
    dt = datetime.fromisoformat(value).replace(tzinfo=timezone.utc).astimezone(TZ)
    return dt.strftime("%d.%m.%Y %H:%M")


# =========================================================================== Ergebnis der Freigabeprüfung
@dataclass
class Gate:
    """``show`` = Teilnehmende sehen das Element (gesperrt oder frei), ``locked`` = gesperrt (nur Titel), ``text``
    = „Verfügbar, sobald …“ (nur bei gesperrt)."""
    show: bool
    locked: bool = False
    text: str = ""


@dataclass
class _Env:
    uid: Optional[int]
    now: datetime
    release_ok: bool
    release_text: str


class Progress:
    """Regeln, Häkchen und berechnete Fakten für einen oder mehrere Kursräume und einige Konten.

    ``Progress(db, channel_ids, user_ids)`` lädt Regeln und Häkchen mit wenigen Abfragen; Fakten (Ansichten, Abgaben,
    Noten) holt es erst bei Bedarf und merkt sie sich."""

    def __init__(self, db: Session, channel_ids: Iterable[int], user_ids: Iterable[Optional[int]] = ()) -> None:
        self.db = db
        self.channel_ids = sorted(set(channel_ids))
        self.user_ids = sorted({u for u in user_ids if u})
        self.rules: dict[tuple[str, int], CompletionRule] = {}
        self.avail: dict[tuple[str, int], dict[str, Any]] = {}
        self.marks: set[tuple[int, str, int]] = set()
        self._facts: dict[tuple[int, str, int], Facts] = {}
        self._loaded: set[tuple[int, str, int]] = set()
        self._titles: dict[tuple[str, int], str] = {}
        self._members: dict[tuple[int, int], set[int]] = {}
        self._channel_of: dict[tuple[str, int], int] = {}
        for chunk in _chunks(self.channel_ids):
            for rule in db.scalars(select(CompletionRule).where(CompletionRule.channel_id.in_(chunk))):
                self.rules[(rule.element_type, rule.element_id)] = rule
                self._channel_of[(rule.element_type, rule.element_id)] = rule.channel_id
            for arule in db.scalars(select(AvailabilityRule).where(AvailabilityRule.channel_id.in_(chunk))):
                if arule.tree:
                    self.avail[(arule.element_type, arule.element_id)] = arule.tree
                    self._channel_of[(arule.element_type, arule.element_id)] = arule.channel_id
            if self.user_ids:
                for m in db.execute(select(CompletionMark.user_id, CompletionMark.element_type,
                                           CompletionMark.element_id)
                                    .where(CompletionMark.channel_id.in_(chunk),
                                           CompletionMark.user_id.in_(self.user_ids))):
                    self.marks.add((m[0], m[1], m[2]))

    # ------------------------------------------------------------------ Fakten
    def _load_facts(self, refs: Iterable[tuple[str, int]], uids: Iterable[Optional[int]]) -> None:
        by_type: dict[str, list[int]] = {}
        wanted = [u for u in uids if u]
        for etype, eid in refs:
            if any((u, etype, eid) not in self._loaded for u in wanted):
                by_type.setdefault(etype, []).append(eid)
        for etype, ids in by_type.items():
            provider = _providers.get(etype)
            channel_ids = {self._channel_of.get((etype, i), 0) for i in ids}
            got: dict[tuple[int, int], Facts] = {}
            if provider is not None:
                for cid in channel_ids or {0}:
                    try:
                        got.update(provider.facts(self.db, cid, wanted, ids))
                    except Exception:  # noqa: BLE001 - ein defekter Anbieter darf die Kursräume nicht blockieren
                        log.exception("Fakten von %s nicht lesbar", etype)
            for u in wanted:
                for i in ids:
                    self._loaded.add((u, etype, i))
                    self._facts[(u, etype, i)] = got.get((u, i), Facts())

    def facts(self, uid: Optional[int], etype: str, eid: int) -> Facts:
        if not uid:
            return Facts()
        self._load_facts([(etype, eid)], [uid])
        return self._facts.get((uid, etype, eid), Facts())

    def prefetch(self, uids: Iterable[Optional[int]], refs: Optional[Iterable[tuple[str, int]]] = None) -> None:
        """Fakten für mehrere Konten und Elemente gebündelt laden (Übersichtstabelle)."""
        self._load_facts(refs if refs is not None else self.rules.keys(), uids)

    # ------------------------------------------------------------------ Abschluss
    def rule(self, etype: str, eid: int) -> Optional[CompletionRule]:
        return self.rules.get((etype, eid))

    def done(self, uid: Optional[int], etype: str, eid: int) -> Optional[bool]:
        """Erledigt? ``None`` = das Element wird nicht verfolgt (keine Abschlussbedingung)."""
        rule = self.rules.get((etype, eid))
        if rule is None:
            return None
        if not uid:
            return False
        if rule.mode == "manual":
            return (uid, etype, eid) in self.marks
        f = self.facts(uid, etype, eid)
        if rule.mode == "viewed":
            return f.viewed
        if rule.mode == "submitted":
            return f.submitted
        if rule.mode == "graded":
            return f.graded
        return f.graded and passes(f, rule.pass_percent)

    def summary(self, uid: Optional[int], refs: Iterable[tuple[str, int]]) -> dict[str, Any]:
        """``{"done": n, "total": n, "percent": 0-100}`` über die verfolgten Elemente aus ``refs``."""
        total = done = 0
        for etype, eid in refs:
            state = self.done(uid, etype, eid)
            if state is None:
                continue
            total += 1
            done += 1 if state else 0
        return {"done": done, "total": total, "percent": round(done * 100 / total) if total else 0}

    # ------------------------------------------------------------------ Freigabe
    def title(self, etype: str, eid: int) -> str:
        key = (etype, eid)
        if key not in self._titles:
            title = ""
            provider = _providers.get(etype)
            if provider is not None:
                cid = self._channel_of.get(key)
                try:
                    for el in provider.elements(self.db, cid or 0) if cid else []:
                        self._titles[(el.type, el.id)] = el.title
                except Exception:  # noqa: BLE001
                    log.exception("Titel von %s nicht lesbar", etype)
                title = self._titles.get(key, "")
            if not title and etype == ELEMENT_ITEM:
                item = self.db.get(ChannelItem, eid)
                title = item.title if item else ""
            self._titles[key] = title or "gelöschtes Element"
        return self._titles[key]

    def _group_name(self, channel_id: int, gid: int) -> str:
        gp = _group_provider
        if gp is not None:
            for g in gp.list_groups(self.db, channel_id):
                if int(g["id"]) == gid:
                    return str(g["name"])
        return "unbekannt"

    def _is_member(self, channel_id: int, uid: Optional[int], gid: int) -> bool:
        gp = _group_provider
        if gp is None or not uid:
            return False
        key = (channel_id, gid)
        if key not in self._members:
            try:
                self._members[key] = set(gp.member_ids(self.db, channel_id, gid))
            except Exception:  # noqa: BLE001
                log.exception("Gruppenmitglieder nicht lesbar")
                self._members[key] = set()
        return uid in self._members[key]

    def _eval(self, node: dict[str, Any], env: _Env, channel_id: int) -> tuple[bool, str]:
        results = []
        for sub in node["items"]:
            results.append(self._eval(sub, env, channel_id) if "op" in sub else self._eval_leaf(sub, env, channel_id))
        if node["op"] == "and":
            bad = [text for ok, text in results if not ok]
            return (not bad), " und ".join(bad)
        if any(ok for ok, _ in results):
            return True, ""
        parts = [text for _, text in results if text]
        text = " oder ".join(parts)
        return False, f"({text})" if len(parts) > 1 else text

    def _eval_leaf(self, leaf: dict[str, Any], env: _Env, channel_id: int) -> tuple[bool, str]:
        kind = leaf["type"]
        if kind == "release":
            return env.release_ok, env.release_text
        if kind == "date":
            start, end = leaf.get("from"), leaf.get("until")
            now = env.now.isoformat(timespec="seconds")
            if start and now < start:
                return False, f"ab {_fmt_dt(start)}"
            if end and now >= end:
                return False, f"im Zeitraum bis {_fmt_dt(end)} (vorbei)"
            return True, ""
        if kind == "group":
            gid = int(leaf["group_id"])
            return self._is_member(channel_id, env.uid, gid), f"Mitglied der Gruppe „{self._group_name(channel_id, gid)}“"
        etype, eid = leaf["element_type"], int(leaf["element_id"])
        self._channel_of.setdefault((etype, eid), channel_id)
        title = self.title(etype, eid)
        if kind == "completed":
            return bool(self.done(env.uid, etype, eid)), f"„{title}“ erledigt"
        f = self.facts(env.uid, etype, eid)
        if kind == "score":
            need = float(leaf["min_percent"])
            ok = f.score_percent is not None and f.score_percent + 1e-9 >= need
            return ok, f"„{title}“ mit mindestens {need:g} % bewertet"
        need_note = float(leaf["max_note"])
        ok = f.note is not None and f.note <= need_note + 1e-9
        return ok, f"„{title}“ mit Note {need_note:g} oder besser bewertet"

    def gate(self, uid: Optional[int], etype: str, eid: int, vis: "logic.Visibility", channel_id: int) -> Gate:
        """Sieht ein/e Teilnehmende/r das Element (``vis`` = Zeitfreigabe des Kursraums), und ist es gesperrt?"""
        if vis.code in ("hidden", "folder_hidden"):
            return Gate(False)
        tree = self.avail.get((etype, eid))
        if not tree:
            return Gate(vis.visible)
        release = has_release(tree)
        if not release and not vis.visible:
            return Gate(False)
        if vis.release_at:
            rtext = f"ab {_fmt_dt(vis.release_at.isoformat(timespec='seconds'))}"
        else:
            rtext = "zur Unterrichtsstunde"
        env = _Env(uid, logic.now_utc(), vis.visible, rtext)
        ok, text = self._eval(tree, env, channel_id)
        if ok:
            return Gate(True)
        return Gate(True, True, text)

    def describe(self, etype: str, eid: int, channel_id: int) -> str:
        """Bedingungen in Worten (für die Lehrkraft), z. B. „„A“ erledigt und Mitglied der Gruppe „B““."""
        tree = self.avail.get((etype, eid))
        if not tree:
            return ""
        env = _Env(None, logic.now_utc(), False, "zur Freigabe des Elements")
        return self._eval(tree, env, channel_id)[1]


# =========================================================================== Pflege
def forget_element(db: Session, etype: str, eid: int) -> None:
    """Regeln und Häkchen eines endgültig entfernten Elements löschen (ohne Commit)."""
    for model in (CompletionRule, AvailabilityRule, CompletionMark):
        db.execute(delete(model).where(model.element_type == etype, model.element_id == eid))


def would_cycle(avail: dict[tuple[str, int], dict[str, Any]], start: tuple[str, int],
                tree: Optional[dict[str, Any]]) -> bool:
    """Würde ``start`` mit dem neuen ``tree`` (direkt oder über andere Elemente) von sich selbst abhängen?"""
    graph = {k: tree_refs(v) for k, v in avail.items() if k != start}
    graph[start] = tree_refs(tree)
    seen: set[tuple[str, int]] = set()
    stack = list(graph[start])
    while stack:
        cur = stack.pop()
        if cur == start:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(graph.get(cur, ()))
    return False


def mask_locked(entry: dict[str, Any], gate: Gate) -> dict[str, Any]:
    """Gesperrtes Element für Teilnehmende: nur Titel, Art und „Verfügbar, sobald …“."""
    for key in ("file", "url"):
        entry[key] = None
    entry["attachments"] = []
    entry["has_body"] = False
    entry["submittable"] = False
    entry.pop("submission", None)
    entry["locked"] = True
    entry["locked_text"] = gate.text
    return entry


# =========================================================================== Gruppen des Kursraums (M1)
class CourseGroups:
    """Gruppen-Anbieter auf Basis der Kursgruppen (``feature_models/channel_groups.py``, Agent M1)."""

    def list_groups(self, db: Session, channel_id: int) -> list[dict[str, Any]]:
        from .feature_models.channel_groups import ChannelGroup, ChannelGroupSet

        sets = {s.id: s.name for s in db.scalars(select(ChannelGroupSet).where(ChannelGroupSet.channel_id == channel_id))}
        groups = list(db.scalars(select(ChannelGroup).where(ChannelGroup.channel_id == channel_id)
                                 .order_by(ChannelGroup.set_id, ChannelGroup.position, ChannelGroup.id)))
        many = len(sets) > 1
        return [{"id": g.id, "name": f"{sets.get(g.set_id, '')}: {g.name}" if many else g.name} for g in groups]

    def member_ids(self, db: Session, channel_id: int, group_id: int) -> set[int]:
        from .feature_models.channel_groups import ChannelGroupMember

        return set(db.scalars(select(ChannelGroupMember.user_id).where(ChannelGroupMember.channel_id == channel_id,
                                                                       ChannelGroupMember.group_id == group_id)))


try:                                                  # ohne die Gruppen-Tabellen bleibt die Bedingung ausgeblendet
    from .feature_models import channel_groups as _channel_groups  # noqa: F401
except ImportError:  # pragma: no cover
    pass
else:
    register_group_provider(CourseGroups())
