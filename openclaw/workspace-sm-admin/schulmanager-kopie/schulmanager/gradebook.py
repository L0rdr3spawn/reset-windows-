"""Notenbuch – reine Rechenlogik (ohne Datenbank und HTTP). Doku: ``docs/NOTENBUCH.md``.

Bausteine
=========
* :class:`Scale` – Notenskala: ``note6`` (1–6 mit Tendenzen), ``punkte15`` (15–0 Punkte), ``prozent``, ``verbal``
  (Text, keine Rechnung), ``bestanden`` (bestanden / nicht bestanden) und ``custom`` (eigene Stufen mit Zahlenwert).
* :class:`Key` – Notenschlüssel: Prozentgrenzen, die erreichte Punkte einer Leistung in eine Note der Skala umrechnen.
* :func:`entry_number` – Zahlenwert einer Eintragung (berücksichtigt Status und Punkte).
* :func:`compute_student` – gewichteter Schnitt je Kategorie (verschachtelt) und gesamt.
* :func:`suggest` – Vorschlagsnote aus dem Gesamtschnitt.
* :func:`risk_for` – Warnung bei gefährdeter Versetzung.

Regeln (kurz)
=============
* Gerechnet wird mit ``Decimal``; Runden ist immer „kaufmännisch“ (0,5 wird aufgerundet, bei Noten also zur
  schlechteren Note, bei Punkten und Prozent zum besseren Wert).
* Tendenzen: ``2+`` = 1,7 und ``2-`` = 2,3 (±0,3); ``1+`` zählt wie ``1`` (1,0), ``6-`` gibt es nicht.
* Der Schnitt einer Kategorie ist der nach Gewicht gemittelte Wert ihrer Noten und Unterkategorien. Was keine
  zählende Note hat, wird nicht mit 0 gerechnet; die Gewichte der übrigen verteilen sich neu.
* Status ``entschuldigt``, ``ausgelassen`` und ``nachschreiben`` zählen nicht; ``unentschuldigt`` zählt als schlechteste
  Note der Skala.
* Die Vorschlagsnote entsteht aus dem auf ``decimals`` Stellen gerundeten Gesamtschnitt (so wie die Lehrkraft ihn sieht).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Optional, Sequence

D = Decimal
ZERO, ONE, HUNDRED = D(0), D(1), D(100)
TENTH3 = D("0.3")

KINDS = ("note6", "punkte15", "prozent", "verbal", "bestanden", "custom")
ROUNDINGS = ("ganz", "tendenz")
MAX_DEPTH = 4

#: Status einer Eintragung. Leer = normal gewertet.
STATUS_LABELS: dict[str, str] = {
    "": "",
    "entschuldigt": "entschuldigt (zählt nicht)",
    "ausgelassen": "ausgelassen (zählt nicht)",
    "nachschreiben": "Nachschreiben (zählt noch nicht)",
    "unentschuldigt": "unentschuldigt gefehlt (ungenügend)",
}
NOT_COUNTED = frozenset({"entschuldigt", "ausgelassen", "nachschreiben"})


def dec(value: Any) -> Optional[Decimal]:
    """Zahl aus Text (deutsches Komma erlaubt) oder ``None``."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return None
    s = str(value).strip().replace(",", ".").replace("−", "-").replace(" ", "")
    if not s:
        return None
    try:
        out = D(s)
    except InvalidOperation:
        return None
    return out if out.is_finite() else None


def quantize(value: Decimal, places: int = 2) -> Decimal:
    """Kaufmännisch runden (0,5 immer auf)."""
    return value.quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP) if value >= 0 else \
        -((-value).quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP))


# ----------------------------------------------------------------------------------------------- Skalen
@dataclass(frozen=True)
class Scale:
    id: str
    name: str
    kind: str
    #: Stufen (Beschriftung, Zahlenwert), für das Runden der Vorschlagsnote; leer bei ``prozent``/``verbal``
    labels: tuple[tuple[str, Decimal], ...] = ()
    higher_better: bool = False
    builtin: bool = True

    @property
    def numeric(self) -> bool:
        return self.kind != "verbal"

    def worst(self) -> Optional[Decimal]:
        if self.kind == "note6":
            return D(6)
        if self.kind in ("punkte15", "prozent", "bestanden"):
            return ZERO
        if self.kind == "custom" and self.labels:
            vals = [v for _, v in self.labels]
            return min(vals) if self.higher_better else max(vals)
        return None

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "kind": self.kind, "builtin": self.builtin,
                "numeric": self.numeric, "higher_better": self.higher_better,
                "labels": [{"label": label, "value": float(v)} for label, v in self.labels]}


def _note6_labels() -> tuple[tuple[str, Decimal], ...]:
    out: list[tuple[str, Decimal]] = []
    for n in range(1, 7):
        if n > 1 and n < 6:
            out.append((f"{n}+", D(n) - TENTH3))
        out.append((str(n), D(n)))
        if n < 6:
            out.append((f"{n}-", D(n) + TENTH3))
    return tuple(out)


#: Tendenzschritte für das Runden: 1, 1-, 2+, 2, 2-, … 5-, 6 (``1+`` wird nie vorgeschlagen)
_NOTE6_STEPS: tuple[tuple[str, Decimal], ...] = tuple(sorted(
    ((label, v) for label, v in _note6_labels() if label != "1+"), key=lambda x: x[1]))

BUILTIN_SCALES: dict[str, Scale] = {
    "note6": Scale("note6", "Noten 1–6 (mit Tendenz)", "note6", _note6_labels(), False),
    "punkte15": Scale("punkte15", "Punkte 15–0 (Oberstufe)", "punkte15",
                      tuple((str(i), D(i)) for i in range(15, -1, -1)), True),
    "prozent": Scale("prozent", "Prozent", "prozent", (), True),
    "verbal": Scale("verbal", "Verbal / Text", "verbal", (), False),
    "bestanden": Scale("bestanden", "Bestanden / nicht bestanden", "bestanden",
                       (("bestanden", ONE), ("nicht bestanden", ZERO)), True),
}
DEFAULT_SCALE = "note6"


def custom_scale(raw: Mapping[str, Any]) -> Scale:
    """Eigene Skala aus der Konfiguration (``{"id","name","labels":[{"label","value"}],"higher_better"}``)."""
    labels = []
    for item in raw.get("labels") or []:
        label = str(item.get("label", "")).strip()
        value = dec(item.get("value"))
        if label and value is not None:
            labels.append((label, value))
    return Scale(str(raw["id"]), str(raw.get("name") or raw["id"]), "custom", tuple(labels),
                 bool(raw.get("higher_better", False)), builtin=False)


def scale_table(custom: Iterable[Mapping[str, Any]] = ()) -> dict[str, Scale]:
    out = dict(BUILTIN_SCALES)
    for raw in custom or []:
        try:
            sc = custom_scale(raw)
        except (KeyError, TypeError):
            continue
        if sc.id not in BUILTIN_SCALES and sc.labels:
            out[sc.id] = sc
    return out


def _norm_label(text: str) -> str:
    return text.strip().replace("−", "-").replace("–", "-").replace(" ", "").lower()


def parse_value(scale: Scale, raw: Any) -> Optional[Decimal]:
    """Zahlenwert einer eingegebenen Note (``None`` = leer oder ungültig)."""
    text = "" if raw is None else str(raw).strip()
    if not text or scale.kind == "verbal":
        return None
    if scale.kind == "note6":
        norm = _norm_label(text)
        for label, v in scale.labels:
            if label == norm:
                return v
        if norm == "1+":
            return ONE
        return None
    if scale.kind == "punkte15":
        v = dec(text)
        return v if v is not None and v == v.to_integral_value() and 0 <= v <= 15 else None
    if scale.kind == "prozent":
        v = dec(text.rstrip("% "))
        return v if v is not None and 0 <= v <= 100 else None
    norm = _norm_label(text)
    if scale.kind == "bestanden":
        if norm in ("bestanden", "b", "ja", "1"):
            return ONE
        if norm in ("nichtbestanden", "nb", "nein", "0"):
            return ZERO
        return None
    for label, v in scale.labels:
        if _norm_label(label) == norm:
            return v
    return None


def is_valid(scale: Scale, raw: Any) -> bool:
    """Eingabe leer (erlaubt) oder in der Skala gültig; ``verbal`` nimmt jeden Text."""
    text = "" if raw is None else str(raw).strip()
    return not text or scale.kind == "verbal" or parse_value(scale, text) is not None


def label_for(scale: Scale, number: Decimal, rounding: str = "ganz") -> str:
    """Beschriftung der Stufe, auf die ``number`` gerundet wird."""
    if scale.kind == "verbal":
        return ""
    if scale.kind == "note6":
        if rounding == "tendenz":
            best = None
            for label, v in _NOTE6_STEPS:                 # aufsteigend; bei Gleichstand die schlechtere Stufe
                if best is None or abs(number - v) <= abs(number - best[1]):
                    best = (label, v)
            return best[0] if best else "6"
        n = int(number.quantize(ONE, rounding=ROUND_HALF_UP))
        return str(min(6, max(1, n)))
    if scale.kind == "punkte15":
        return str(min(15, max(0, int(number.quantize(ONE, rounding=ROUND_HALF_UP)))))
    if scale.kind == "prozent":
        return str(min(100, max(0, int(number.quantize(ONE, rounding=ROUND_HALF_UP)))))
    if scale.kind == "bestanden":      # mindestens die Hälfte der Leistungen bestanden
        return "bestanden" if number >= D("0.5") else "nicht bestanden"
    best_l: Optional[tuple[str, Decimal]] = None
    for label, v in scale.labels:
        if best_l is None:
            best_l = (label, v)
            continue
        d_new, d_old = abs(number - v), abs(number - best_l[1])
        worse = (v < best_l[1]) if scale.higher_better else (v > best_l[1])
        if d_new < d_old or (d_new == d_old and worse):
            best_l = (label, v)
    return best_l[0] if best_l else ""


# ----------------------------------------------------------------------------------------- Notenschlüssel
@dataclass(frozen=True)
class Key:
    id: str
    name: str
    scale_id: str
    #: (Mindestprozent, Note) absteigend nach Prozent; unter der letzten Grenze gilt die letzte Note
    steps: tuple[tuple[Decimal, str], ...]
    builtin: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "scale_id": self.scale_id, "builtin": self.builtin,
                "steps": [{"min_percent": float(p), "label": label} for p, label in self.steps]}


def _steps(pairs: Sequence[tuple[str, str]]) -> tuple[tuple[Decimal, str], ...]:
    return tuple((D(p), g) for p, g in pairs)


BUILTIN_KEYS: dict[str, Key] = {
    "standard6": Key("standard6", "Standard 1–6 (ganze Noten)", "note6",
                     _steps([("87", "1"), ("73", "2"), ("59", "3"), ("45", "4"), ("18", "5"), ("0", "6")])),
    "tendenz6": Key("tendenz6", "Standard 1–6 mit Tendenz", "note6", _steps([
        ("95", "1"), ("90", "1-"), ("85", "2+"), ("80", "2"), ("75", "2-"), ("70", "3+"), ("65", "3"), ("60", "3-"),
        ("55", "4+"), ("50", "4"), ("45", "4-"), ("39", "5+"), ("33", "5"), ("27", "5-"), ("0", "6")])),
    "oberstufe15": Key("oberstufe15", "Oberstufe 15–0 Punkte", "punkte15", _steps([
        ("95", "15"), ("90", "14"), ("85", "13"), ("80", "12"), ("75", "11"), ("70", "10"), ("65", "9"), ("60", "8"),
        ("55", "7"), ("50", "6"), ("45", "5"), ("39", "4"), ("33", "3"), ("27", "2"), ("20", "1"), ("0", "0")])),
    "bestanden50": Key("bestanden50", "Bestanden ab 50 %", "bestanden",
                       _steps([("50", "bestanden"), ("0", "nicht bestanden")])),
}
DEFAULT_KEYS = {"note6": "standard6", "punkte15": "oberstufe15", "bestanden": "bestanden50"}


def custom_key(raw: Mapping[str, Any]) -> Key:
    steps = []
    for item in raw.get("steps") or []:
        p, label = dec(item.get("min_percent")), str(item.get("label", "")).strip()
        if p is not None and label and 0 <= p <= 100:
            steps.append((p, label))
    steps.sort(key=lambda x: -x[0])
    return Key(str(raw["id"]), str(raw.get("name") or raw["id"]), str(raw.get("scale_id", "note6")), tuple(steps),
               builtin=False)


def key_table(custom: Iterable[Mapping[str, Any]] = ()) -> dict[str, Key]:
    out = dict(BUILTIN_KEYS)
    for raw in custom or []:
        try:
            k = custom_key(raw)
        except (KeyError, TypeError):
            continue
        if k.id not in BUILTIN_KEYS and k.steps:
            out[k.id] = k
    return out


def percent_of(points: Decimal, max_points: Decimal) -> Decimal:
    return points * HUNDRED / max_points


def apply_key(key: Key, points: Decimal, max_points: Decimal) -> str:
    """Note für erreichte Punkte (Grenzen gelten „ab“ – genau auf der Grenze zählt schon die bessere Note)."""
    pct = percent_of(points, max_points)
    for minimum, label in key.steps:
        if pct >= minimum:
            return label
    return key.steps[-1][1]


def key_for(scale: Scale, key_id: str, keys: Mapping[str, Key], defaults: Optional[Mapping[str, str]] = None
            ) -> Optional[Key]:
    """Notenschlüssel für eine Skala: ausdrücklich gewählt → Schulstandard → eingebauter Standard."""
    for kid in (key_id, (defaults or {}).get(scale.id, ""), DEFAULT_KEYS.get(scale.kind, "")):
        k = keys.get(kid) if kid else None
        if k is not None and k.scale_id == scale.id:
            return k
    return None


# ------------------------------------------------------------------------------------------ Eintragungen
def entry_number(scale: Scale, key: Optional[Key], max_points: Optional[Decimal], status: str, raw: Any
                 ) -> Optional[Decimal]:
    """Zahlenwert, der in den Schnitt eingeht – ``None`` = zählt nicht (leer, ausgelassen, entschuldigt …)."""
    if status in NOT_COUNTED or not scale.numeric:
        return None
    if status == "unentschuldigt":
        return scale.worst()
    value = dec(raw)
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None
    if max_points is not None and max_points > 0:
        if value is None or value < 0:
            return None
        if scale.kind == "prozent":
            return min(HUNDRED, percent_of(value, max_points))
        if key is None:
            return None
        return parse_value(scale, apply_key(key, value, max_points))
    return parse_value(scale, text)


def entry_label(scale: Scale, key: Optional[Key], max_points: Optional[Decimal], status: str, raw: Any) -> str:
    """Angezeigte Note einer Eintragung (bei Punkten die umgerechnete Note, sonst die Eingabe)."""
    text = "" if raw is None else str(raw).strip()
    if status == "unentschuldigt":
        return {"note6": "6", "punkte15": "0", "prozent": "0", "bestanden": "nicht bestanden"}.get(scale.kind, "")
    if status in NOT_COUNTED or not text:
        return ""
    if max_points is not None and max_points > 0 and scale.numeric:
        value = dec(text)
        if value is None or value < 0:
            return ""
        if scale.kind == "prozent":
            return str(quantize(min(HUNDRED, percent_of(value, max_points)), 1)).rstrip("0").rstrip(".")
        return apply_key(key, value, max_points) if key is not None else ""
    return text


# ----------------------------------------------------------------------------------------------- Rechnung
@dataclass
class CatNode:
    id: int
    parent: Optional[int]
    weight: Decimal = ONE


@dataclass
class ItemNode:
    id: int
    category: Optional[int]
    weight: Decimal = ONE


@dataclass
class Result:
    categories: dict[int, Optional[Decimal]] = field(default_factory=dict)
    overall: Optional[Decimal] = None
    counted: int = 0


def compute_student(cats: Sequence[CatNode], items: Sequence[ItemNode], numbers: Mapping[int, Optional[Decimal]]
                    ) -> Result:
    """Gewichtete Schnitte einer Person.

    ``numbers``: Zahlenwert je Leistung (``None`` = zählt nicht). Gewichte ≤ 0 zählen nicht. Kategorien ohne
    zählende Note haben den Schnitt ``None``.
    """
    child_cats: dict[Optional[int], list[CatNode]] = {}
    child_items: dict[Optional[int], list[ItemNode]] = {}
    known = {c.id for c in cats}
    for c in cats:
        child_cats.setdefault(c.parent if c.parent in known else None, []).append(c)
    for it in items:
        child_items.setdefault(it.category if it.category in known else None, []).append(it)
    out = Result()

    def node(node_id: Optional[int], depth: int) -> Optional[tuple[Decimal, int]]:
        total, weight, counted = ZERO, ZERO, 0
        for it in child_items.get(node_id, ()):
            v = numbers.get(it.id)
            if v is not None and it.weight > 0:
                total += v * it.weight
                weight += it.weight
                counted += 1
        if depth < MAX_DEPTH:
            for c in child_cats.get(node_id, ()):
                sub = node(c.id, depth + 1)
                out.categories[c.id] = sub[0] if sub else None
                if sub is not None and c.weight > 0:
                    total += sub[0] * c.weight
                    weight += c.weight
                    counted += sub[1]
        return (total / weight, counted) if weight > 0 else None

    res = node(None, 0)
    if res is not None:
        out.overall, out.counted = res
    return out


def suggest(scale: Scale, average: Optional[Decimal], rounding: str = "ganz", decimals: int = 2
            ) -> tuple[Optional[Decimal], str]:
    """``(auf decimals gerundeter Schnitt, Vorschlagsnote)``; ohne Schnitt oder bei Textskala ``(None, "")``."""
    if average is None or not scale.numeric:
        return None, ""
    avg = quantize(average, decimals)
    return avg, label_for(scale, avg, rounding)


def is_overridden(proposal: str, final: str) -> bool:
    """Festgelegte Note weicht vom Vorschlag ab (nur sinnvoll, wenn es einen Vorschlag gibt)."""
    return bool(proposal) and bool(final.strip()) and _norm_label(final) != _norm_label(proposal)


# ---------------------------------------------------------------------------------------------- Warnung
DEFAULT_RISK: dict[str, Any] = {
    "enabled": True,
    "min_grade": 5,          # Note 5 oder 6 zählt als Defizit (1–6)
    "max_points": 4,         # 4 Punkte oder weniger zählt als Defizit (Oberstufe)
    "core_count": 1,         # Warnung bei so vielen Defiziten in Hauptfächern (0 = aus)
    "any_count": 2,          # Warnung bei so vielen Defiziten in allen Fächern (0 = aus)
}


def risk_config(raw: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    out = dict(DEFAULT_RISK)
    for k in DEFAULT_RISK:
        if raw and k in raw:
            out[k] = raw[k]
    return out


def is_deficit(scale: Scale, label: str, cfg: Mapping[str, Any]) -> bool:
    """Ist die Note ein Defizit im Sinne der Versetzungswarnung?"""
    if not label:
        return False
    v = parse_value(scale, label)
    if v is None:
        return False
    if scale.kind == "note6":
        return int(v.quantize(ONE, rounding=ROUND_HALF_UP)) >= int(cfg["min_grade"])   # 5+, 5, 5- und 6
    if scale.kind == "punkte15":
        return v <= D(cfg["max_points"])
    return False


def risk_for(deficits: Iterable[tuple[bool, bool]], cfg: Mapping[str, Any]) -> list[str]:
    """Gründe der Warnung. ``deficits``: je Defizit-Fach ``(Hauptfach?, True)``; leer = keine Warnung."""
    if not cfg.get("enabled", True):
        return []
    rows = list(deficits)
    core = sum(1 for is_core, _ in rows if is_core)
    reasons = []
    if cfg["core_count"] and core >= int(cfg["core_count"]):
        reasons.append(f"{core} Hauptfach mit Defizit" if core == 1 else f"{core} Hauptfächer mit Defizit")
    if cfg["any_count"] and len(rows) >= int(cfg["any_count"]):
        reasons.append(f"{len(rows)} Fächer mit Defizit")
    return reasons
