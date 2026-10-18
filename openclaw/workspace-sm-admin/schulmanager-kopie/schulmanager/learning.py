"""Lernaktivitäten im Kursraum – reine Logik ohne Datenbank (Doku: docs/LERNAKTIVITAETEN.md).

* **Abstimmung** (:func:`normalize_poll`, :func:`clean_choices`, :func:`results_visible`) – eine oder mehrere
  Antworten, anonym oder namentlich, Ergebnisse sofort / nach der eigenen Stimme / nach Ende.
* **Fragen und Selbsttest** (:func:`normalize_question`, :func:`public_question`, :func:`grade_question`,
  :func:`grade_attempt`) – Einfach-/Mehrfachauswahl, Wahr/Falsch, Lückentext mit exakter Antwort, Zuordnung und Zahl
  mit Toleranz; Mischen mit festem Startwert, damit ein Versuch bei jedem Aufruf gleich aussieht.
* **GIFT** (:func:`parse_gift`, :func:`export_gift`) – Austauschformat der Moodle-Fragensammlung.
* **Umfrage** (:func:`aggregate_survey`) – Auswertung der Antworten, die :mod:`schulmanager.forms` prüft (gleiche
  Feldarten wie der Formular-Baukasten, dazu die Skala 1–5).
"""
from __future__ import annotations

import math
import random
import re
from typing import Any, Optional

from .forms import FormError, clean_text

# ----------------------------------------------------------------------------- Abstimmung
POLL_RESULTS: dict[str, str] = {
    "live": "Sofort sichtbar", "after_vote": "Nach der eigenen Stimme", "after_end": "Erst nach dem Ende",
}
MAX_POLL_OPTIONS = 20
MIN_POLL_OPTIONS = 2


class LearningError(FormError):
    """Ungültige Eingabe (Text ist für Nutzer/innen gedacht)."""


def normalize_poll(raw: Any, *, with_texts: bool = True) -> dict:
    """Prüft die Einstellungen einer Abstimmung. ``with_texts=False`` (Chat): Frage und Antworten stehen
    Ende-zu-Ende verschlüsselt in der Nachricht, der Server kennt nur die Anzahl der Antworten."""
    if not isinstance(raw, dict):
        raise LearningError("Ungültige Abstimmung")
    if with_texts:
        question = clean_text(raw.get("question"), 300)
        if not question:
            raise LearningError("Bitte eine Frage eingeben")
        options = [clean_text(o, 200) for o in (raw.get("options") or []) if clean_text(o, 200)]
        if len(set(o.casefold() for o in options)) != len(options):
            raise LearningError("Die Antworten müssen sich unterscheiden")
        count = len(options)
    else:
        question, options = "", []
        try:
            count = int(raw.get("option_count"))
        except (TypeError, ValueError):
            raise LearningError("Bitte mindestens zwei Antworten angeben") from None
    if not MIN_POLL_OPTIONS <= count <= MAX_POLL_OPTIONS:
        raise LearningError(f"Bitte {MIN_POLL_OPTIONS} bis {MAX_POLL_OPTIONS} Antworten angeben")
    multiple = bool(raw.get("multiple"))
    max_choices: Optional[int] = None
    if multiple and raw.get("max_choices") not in (None, ""):
        try:
            max_choices = int(raw["max_choices"])
        except (TypeError, ValueError):
            raise LearningError("Höchstzahl der Antworten: bitte eine ganze Zahl angeben") from None
        if not 1 <= max_choices <= count:
            raise LearningError(f"Höchstzahl der Antworten: erlaubt sind 1 bis {count}")
        if max_choices == count:
            max_choices = None
    results = raw.get("results") if raw.get("results") in POLL_RESULTS else "live"
    return {"question": question, "options": options, "option_count": count, "multiple": multiple,
            "max_choices": max_choices, "anonymous": bool(raw.get("anonymous")), "results": results}


def clean_choices(choices: Any, option_count: int, multiple: bool, max_choices: Optional[int]) -> list[int]:
    """Gewählte Antworten prüfen (Indizes ab 0, ohne Doppelte)."""
    if not isinstance(choices, list):
        raise LearningError("Bitte eine Antwort wählen")
    picked: list[int] = []
    for c in choices:
        if isinstance(c, bool) or not isinstance(c, int):
            raise LearningError("Ungültige Antwort")
        if not 0 <= c < option_count:
            raise LearningError("Ungültige Antwort")
        if c not in picked:
            picked.append(c)
    if not picked:
        raise LearningError("Bitte eine Antwort wählen")
    if not multiple and len(picked) > 1:
        raise LearningError("Es ist nur eine Antwort erlaubt")
    if multiple and max_choices and len(picked) > max_choices:
        raise LearningError(f"Es sind höchstens {max_choices} Antworten erlaubt")
    return sorted(picked)


def results_visible(mode: str, *, voted: bool, closed: bool, staff: bool = False) -> bool:
    """Darf diese Person das Ergebnis sehen? ``staff`` = wer die Abstimmung eingestellt hat bzw. Lehrende."""
    if staff or closed or mode == "live":
        return True
    return mode == "after_vote" and voted


# ----------------------------------------------------------------------------- Fragen
QUESTION_TYPES: dict[str, str] = {
    "single": "Einfachauswahl", "multi": "Mehrfachauswahl", "truefalse": "Wahr / Falsch",
    "cloze": "Lückentext", "matching": "Zuordnung", "numeric": "Zahl mit Toleranz",
}
GAP_RE = re.compile(r"_{3,}")
MAX_Q_OPTIONS = 10
MAX_Q_TEXT = 4000
MAX_POINTS = 100.0
REVIEW_MODES: dict[str, str] = {"none": "Nichts anzeigen", "score": "Nur den Punktestand", "full": "Punktestand und Lösungen"}


def _points(raw: Any) -> float:
    if raw in (None, ""):
        return 1.0
    try:
        value = float(str(raw).replace(",", "."))
    except ValueError:
        raise LearningError("Punkte: bitte eine Zahl angeben") from None
    if not (math.isfinite(value) and 0 <= value <= MAX_POINTS):
        raise LearningError(f"Punkte: erlaubt sind 0 bis {int(MAX_POINTS)}")
    return round(value, 2)


def _number(raw: Any, label: str) -> float:
    try:
        value = float(str(raw).strip().replace(",", "."))
    except ValueError:
        raise LearningError(f"{label}: bitte eine Zahl angeben") from None
    if not math.isfinite(value) or abs(value) > 1e12:
        raise LearningError(f"{label}: bitte eine Zahl angeben")
    return value


def normalize_question(raw: Any) -> dict:
    """Prüft und bereinigt eine Frage (``LearningError`` mit deutschem Text). Ergebnis enthält die Lösung."""
    if not isinstance(raw, dict):
        raise LearningError("Ungültige Frage")
    qtype = str(raw.get("type") or "")
    if qtype not in QUESTION_TYPES:
        raise LearningError("Bitte die Art der Frage wählen")
    text = clean_text(raw.get("text"), MAX_Q_TEXT, multiline=True)
    if not text:
        raise LearningError("Bitte den Fragetext eingeben")
    q: dict[str, Any] = {"type": qtype, "text": text, "points": _points(raw.get("points")),
                         "feedback": clean_text(raw.get("feedback"), 1000, multiline=True),
                         "category": clean_text(raw.get("category"), 60)}
    if qtype in ("single", "multi"):
        options = []
        for o in raw.get("options") or []:
            if not isinstance(o, dict):
                continue
            label = clean_text(o.get("text"), 300)
            if label:
                options.append({"text": label, "correct": bool(o.get("correct")),
                                "feedback": clean_text(o.get("feedback"), 300)})
        if not 2 <= len(options) <= MAX_Q_OPTIONS:
            raise LearningError(f"Bitte 2 bis {MAX_Q_OPTIONS} Antworten angeben")
        right = sum(1 for o in options if o["correct"])
        if qtype == "single" and right != 1:
            raise LearningError("Bei der Einfachauswahl muss genau eine Antwort richtig sein")
        if qtype == "multi" and right < 1:
            raise LearningError("Bitte mindestens eine richtige Antwort markieren")
        q["options"] = options
    elif qtype == "truefalse":
        value = raw.get("correct")
        if isinstance(value, str):
            value = value.strip().lower() in ("true", "wahr", "1", "ja")
        q["correct"] = bool(value)
    elif qtype == "cloze":
        gaps_raw = raw.get("gaps")
        marks = len(GAP_RE.findall(text))
        if marks < 1:
            raise LearningError("Der Text braucht mindestens eine Lücke (drei Unterstriche: ___)")
        if not isinstance(gaps_raw, list) or len(gaps_raw) != marks:
            raise LearningError(f"Bitte zu jeder der {marks} Lücke(n) die richtige Antwort angeben")
        gaps: list[list[str]] = []
        for g in gaps_raw:
            items = g if isinstance(g, list) else [g]
            accepted = [clean_text(a, 120) for a in items if clean_text(a, 120)]
            accepted = list(dict.fromkeys(accepted))
            if not accepted:
                raise LearningError("Zu jeder Lücke gehört mindestens eine richtige Antwort")
            gaps.append(accepted[:10])
        q["gaps"] = gaps
        q["case_sensitive"] = bool(raw.get("case_sensitive"))
    elif qtype == "matching":
        pairs = []
        for p in raw.get("pairs") or []:
            if not isinstance(p, dict):
                continue
            left, right = clean_text(p.get("left"), 200), clean_text(p.get("right"), 200)
            if left or right:
                if not (left and right):
                    raise LearningError("Zu jedem Eintrag der Zuordnung gehören zwei Teile")
                pairs.append({"left": left, "right": right})
        if not 2 <= len(pairs) <= MAX_Q_OPTIONS:
            raise LearningError(f"Bitte 2 bis {MAX_Q_OPTIONS} Paare angeben")
        if len({p["left"].casefold() for p in pairs}) != len(pairs):
            raise LearningError("Die linken Teile müssen sich unterscheiden")
        q["pairs"] = pairs
    else:  # numeric
        q["value"] = _number(raw.get("value"), "Richtige Zahl")
        tol = _number(raw.get("tolerance"), "Toleranz") if raw.get("tolerance") not in (None, "") else 0.0
        if tol < 0:
            raise LearningError("Toleranz: bitte eine Zahl ab 0 angeben")
        q["tolerance"] = tol
        q["unit"] = clean_text(raw.get("unit"), 20)
    return q


def question_title(q: dict, limit: int = 80) -> str:
    """Kurzer Name einer Frage aus dem Text (Listen)."""
    text = GAP_RE.sub("…", " ".join(str(q.get("text") or "").split()))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def max_points(questions: list[dict]) -> float:
    return round(sum(float(q.get("points") or 0) for q in questions), 2)


def _rng(seed: int, salt: str) -> random.Random:
    return random.Random(f"{seed}:{salt}")


def matching_rights(q: dict) -> list[str]:
    """Rechte Teile der Zuordnung (ohne Doppelte, in Eingabereihenfolge)."""
    return list(dict.fromkeys(p["right"] for p in q.get("pairs") or []))


def public_question(q: dict, qid: int, seed: int, *, shuffle_answers: bool) -> dict:
    """Frage ohne Lösung für die Schülerin / den Schüler. Antworten werden – bei festem ``seed`` immer gleich – gemischt;
    die Kennungen (``id``) bleiben die der gespeicherten Frage."""
    out: dict[str, Any] = {"id": qid, "type": q["type"], "text": q["text"], "points": q.get("points", 1)}
    rng = _rng(seed, f"a{qid}")
    if q["type"] in ("single", "multi"):
        opts = [{"id": i, "text": o["text"]} for i, o in enumerate(q["options"])]
        if shuffle_answers:
            rng.shuffle(opts)
        out["options"] = opts
    elif q["type"] == "cloze":
        out["gaps"] = len(q["gaps"])
    elif q["type"] == "matching":
        rights = [{"id": i, "text": t} for i, t in enumerate(matching_rights(q))]
        lefts = [{"id": i, "text": p["left"]} for i, p in enumerate(q["pairs"])]
        if shuffle_answers:
            rng.shuffle(rights)
            rng.shuffle(lefts)
        out["lefts"], out["rights"] = lefts, rights
    elif q["type"] == "numeric":
        out["unit"] = q.get("unit", "")
    return out


def _norm_gap(value: Any, case_sensitive: bool) -> str:
    text = " ".join(str(value or "").split())
    return text if case_sensitive else text.casefold()


def parse_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    try:
        number = float(str(value).strip().replace(",", ".").replace(" ", ""))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def clean_answer(q: dict, raw: Any) -> Any:
    """Antwort einer Schülerin / eines Schülers prüfen und vereinheitlichen; ``None`` = Antwort zurücknehmen."""
    if raw is None or raw == "" or raw == [] or raw == {}:
        return None
    kind = q["type"]
    if kind == "single":
        if isinstance(raw, bool) or not isinstance(raw, int) or not 0 <= raw < len(q["options"]):
            raise LearningError("Ungültige Antwort")
        return raw
    if kind == "multi":
        if not isinstance(raw, list):
            raise LearningError("Ungültige Antwort")
        ids = []
        for a in raw:
            if isinstance(a, bool) or not isinstance(a, int) or not 0 <= a < len(q["options"]):
                raise LearningError("Ungültige Antwort")
            if a not in ids:
                ids.append(a)
        return sorted(ids) or None
    if kind == "truefalse":
        if isinstance(raw, bool):
            return raw
        if raw in ("true", "false"):
            return raw == "true"
        raise LearningError("Ungültige Antwort")
    if kind == "cloze":
        if not isinstance(raw, list):
            raise LearningError("Ungültige Antwort")
        texts = [clean_text(a, 200) for a in raw[: len(q["gaps"])]]
        texts += [""] * (len(q["gaps"]) - len(texts))
        return texts if any(texts) else None
    if kind == "matching":
        if not isinstance(raw, dict):
            raise LearningError("Ungültige Antwort")
        rights = len(matching_rights(q))
        out = {}
        for key, val in raw.items():
            if val in (None, ""):
                continue
            if not str(key).isdigit() or int(key) >= len(q["pairs"]) or isinstance(val, bool)                     or not isinstance(val, int) or not 0 <= val < rights:
                raise LearningError("Ungültige Antwort")
            out[str(int(key))] = val
        return out or None
    text = clean_text(raw, 40)
    if parse_number(text) is None:
        raise LearningError("Bitte eine Zahl eingeben")
    return text


def is_answered(q: dict, answer: Any) -> bool:
    kind = q["type"]
    if kind == "single":
        return isinstance(answer, int) and not isinstance(answer, bool)
    if kind == "multi":
        return isinstance(answer, list) and bool(answer)
    if kind == "truefalse":
        return isinstance(answer, bool) or answer in ("true", "false")
    if kind == "cloze":
        return isinstance(answer, list) and any(str(a or "").strip() for a in answer)
    if kind == "matching":
        return isinstance(answer, dict) and bool(answer)
    return parse_number(answer) is not None


def grade_question(q: dict, answer: Any) -> float:
    """Anteil der Punkte (0 bis 1). Unbeantwortet oder fehlerhaft = 0."""
    kind = q["type"]
    try:
        if kind == "single":
            return 1.0 if isinstance(answer, int) and not isinstance(answer, bool) \
                and 0 <= answer < len(q["options"]) and q["options"][answer]["correct"] else 0.0
        if kind == "multi":
            ids = {a for a in (answer if isinstance(answer, list) else []) if isinstance(a, int)
                   and not isinstance(a, bool) and 0 <= a < len(q["options"])}
            right = {i for i, o in enumerate(q["options"]) if o["correct"]}
            return max(0.0, (len(ids & right) - len(ids - right)) / len(right))
        if kind == "truefalse":
            given = answer if isinstance(answer, bool) else {"true": True, "false": False}.get(str(answer), None)
            return 1.0 if given is not None and given == q["correct"] else 0.0
        if kind == "cloze":
            given = answer if isinstance(answer, list) else []
            cs = bool(q.get("case_sensitive"))
            hits = 0
            for i, accepted in enumerate(q["gaps"]):
                if i < len(given) and _norm_gap(given[i], cs) in {_norm_gap(a, cs) for a in accepted}:
                    hits += 1
            return hits / len(q["gaps"])
        if kind == "matching":
            given = answer if isinstance(answer, dict) else {}
            rights = matching_rights(q)
            hits = 0
            for i, pair in enumerate(q["pairs"]):
                pick = given.get(str(i), given.get(i))
                if isinstance(pick, int) and not isinstance(pick, bool) and 0 <= pick < len(rights) \
                        and rights[pick] == pair["right"]:
                    hits += 1
            return hits / len(q["pairs"])
        if kind == "numeric":
            number = parse_number(answer)
            if number is None:
                return 0.0
            return 1.0 if abs(number - q["value"]) <= q.get("tolerance", 0.0) + 1e-9 else 0.0
    except (KeyError, TypeError, ZeroDivisionError):
        return 0.0
    return 0.0


def solution_view(q: dict) -> dict:
    """Richtige Lösung zur Anzeige (nach Abschluss bzw. nach der Rückmeldung zur Frage)."""
    kind = q["type"]
    if kind in ("single", "multi"):
        return {"correct": [i for i, o in enumerate(q["options"]) if o["correct"]]}
    if kind == "truefalse":
        return {"correct": q["correct"]}
    if kind == "cloze":
        return {"accepted": q["gaps"]}
    if kind == "matching":
        rights = matching_rights(q)
        return {"pairs": [{"left": i, "right": rights.index(p["right"])} for i, p in enumerate(q["pairs"])]}
    return {"value": q["value"], "tolerance": q.get("tolerance", 0.0), "unit": q.get("unit", "")}


def feedback_view(q: dict, answer: Any) -> dict:
    """Rückmeldung zu einer Antwort: allgemeiner Text und Hinweise zu den gewählten Antworten."""
    out: dict[str, Any] = {"general": q.get("feedback", ""), "options": {}}
    if q["type"] in ("single", "multi"):
        picked = answer if isinstance(answer, list) else [answer]
        for a in picked:
            if isinstance(a, int) and not isinstance(a, bool) and 0 <= a < len(q["options"]) \
                    and q["options"][a].get("feedback"):
                out["options"][str(a)] = q["options"][a]["feedback"]
    return out


def grade_attempt(snapshot: list[dict], answers: dict) -> tuple[float, float, list[dict]]:
    """Wertet einen Versuch aus. ``snapshot`` = ``[{"qid", "q"}]``, ``answers`` = ``{str(qid): Antwort}``.
    Ergebnis: (erreichte Punkte, mögliche Punkte, Ergebnis je Frage)."""
    rows = []
    total = got = 0.0
    for item in snapshot:
        q, qid = item["q"], item["qid"]
        pts = float(q.get("points") or 0)
        answer = answers.get(str(qid))
        frac = grade_question(q, answer) if is_answered(q, answer) else 0.0
        earned = round(pts * frac, 2)
        total += pts
        got += earned
        rows.append({"qid": qid, "points": earned, "max": pts, "fraction": round(frac, 4),
                     "answered": is_answered(q, answer), "correct": frac >= 0.999999})
    return round(got, 2), round(total, 2), rows


def percent(points: float, maximum: float) -> float:
    return round(100.0 * points / maximum, 1) if maximum > 0 else 0.0


def build_order(question_ids: list[int], seed: int, shuffle: bool) -> list[int]:
    order = list(question_ids)
    if shuffle:
        _rng(seed, "q").shuffle(order)
    return order


# ----------------------------------------------------------------------------- GIFT (Import/Export)
_GIFT_SPECIAL = "~=#{}:"


def _unescape(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            out.append("\n" if nxt == "n" else nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _escape(text: str) -> str:
    out = []
    for ch in str(text):
        if ch == "\\" or ch in _GIFT_SPECIAL:
            out.append("\\" + ch)
        elif ch == "\n":
            out.append("\\n")
        elif ch >= " ":
            out.append(ch)
    return "".join(out)


def _find_unescaped(text: str, target: str, start: int = 0) -> int:
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == target:
            return i
        i += 1
    return -1


def _split_tokens(body: str) -> list[tuple[str, str]]:
    """``=`` / ``~`` / ``#``-Abschnitte des Antwortteils: [(Zeichen, Text)]."""
    tokens: list[tuple[str, str]] = []
    mark, buf = "", []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            buf.append(body[i:i + 2])
            i += 2
            continue
        if ch in "=~":
            if mark or "".join(buf).strip():
                tokens.append((mark, "".join(buf)))
            mark, buf = ch, []
        else:
            buf.append(ch)
        i += 1
    if mark or "".join(buf).strip():
        tokens.append((mark, "".join(buf)))
    return tokens


def _split_feedback(text: str) -> tuple[str, str]:
    at = _find_unescaped(text, "#")
    if at < 0:
        return text.strip(), ""
    return text[:at].strip(), text[at + 1:].strip()


def _gift_block(block: str) -> Optional[dict]:
    text = block.strip()
    if not text:
        return None
    title = ""
    if text.startswith("::"):
        end = text.find("::", 2)
        if end > 1:
            title, text = text[2:end].strip(), text[end + 2:].strip()
    text = re.sub(r"^\[(html|markdown|plain|moodle)\]", "", text).strip()
    open_at = _find_unescaped(text, "{")
    close_at = _find_unescaped(text, "}", open_at + 1) if open_at >= 0 else -1
    if open_at < 0 or close_at < 0:
        raise LearningError("keine Antworten in { } gefunden (Beschreibungstext wird nicht übernommen)")
    head, body, tail = text[:open_at], text[open_at + 1:close_at], text[close_at + 1:]
    question = _unescape(head).strip()
    after = _unescape(tail).strip()
    raw: dict[str, Any] = {"category": _unescape(title)[:60]}
    stripped = body.strip()
    word = re.sub(r"\s*#.*$", "", stripped, flags=re.S).strip().upper()
    if word in ("T", "TRUE", "F", "FALSE"):
        raw.update(type="truefalse", text=question, correct=word in ("T", "TRUE"),
                   feedback=_unescape(_split_feedback(stripped)[1]))
        return raw
    if stripped.startswith("#"):
        spec = stripped[1:].strip()
        spec = re.sub(r"^=", "", spec).strip()
        first = re.split(r"\s+=|\s*~", spec)[0]
        value_part, feedback = _split_feedback(first)
        range_m = re.fullmatch(r"\s*(-?[\d.,eE+-]+)\s*\.\.\s*(-?[\d.,eE+-]+)\s*", value_part)
        if range_m:
            low, high = parse_number(range_m.group(1)), parse_number(range_m.group(2))
            if low is None or high is None:
                raise LearningError("Zahlbereich nicht lesbar")
            raw.update(type="numeric", text=question, value=(low + high) / 2, tolerance=abs(high - low) / 2,
                       feedback=_unescape(feedback))
            return raw
        num, _, tol = value_part.partition(":")
        raw.update(type="numeric", text=question, value=num.strip(), tolerance=tol.strip() or 0,
                   feedback=_unescape(feedback))
        return raw
    if "->" in body:
        pairs = []
        for mark, tok in _split_tokens(body):
            if mark != "=" or "->" not in tok:
                continue
            left, right = tok.split("->", 1)
            pairs.append({"left": _unescape(left).strip(), "right": _unescape(_split_feedback(right)[0])})
        raw.update(type="matching", text=question, pairs=pairs)
        return raw
    tokens = _split_tokens(body)
    if not tokens:
        raise LearningError("keine Antworten gefunden")
    only_equal = all(mark == "=" for mark, _ in tokens)
    if only_equal:
        accepted = []
        feedback = ""
        for _mark, tok in tokens:
            val, fb = _split_feedback(re.sub(r"^%[-\d.]+%", "", tok.strip()))
            accepted.append(_unescape(val).strip())
            feedback = feedback or fb
        full = f"{question} ___ {after}".strip() if after else f"{question} ___".strip()
        raw.update(type="cloze", text=full, gaps=[accepted], feedback=_unescape(feedback))
        return raw
    options = []
    weighted = False
    for mark, tok in tokens:
        tok = tok.strip()
        weight_m = re.match(r"^%(-?[\d.]+)%", tok)
        weight = None
        if weight_m:
            weighted = True
            weight = float(weight_m.group(1))
            tok = tok[weight_m.end():]
        label, fb = _split_feedback(tok)
        correct = (weight > 0) if weight is not None else mark == "="
        options.append({"text": _unescape(label).strip(), "correct": correct, "feedback": _unescape(fb)})
    right = sum(1 for o in options if o["correct"])
    raw.update(type="multi" if weighted and right > 1 else "single", text=question, options=options)
    return raw


def parse_gift(source: str, *, limit: int = 200) -> tuple[list[dict], list[str]]:
    """GIFT-Text → (geprüfte Fragen, Fehlermeldungen je übersprungener Frage)."""
    text = (source or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln for ln in text.split("\n") if not ln.lstrip().startswith("//")]
    blocks = re.split(r"\n\s*\n", "\n".join(lines))
    questions: list[dict] = []
    errors: list[str] = []
    number = 0
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("$"):
            continue
        number += 1
        if len(questions) >= limit:
            errors.append(f"Mehr als {limit} Fragen – der Rest wurde nicht übernommen")
            break
        try:
            raw = _gift_block(block)
            if raw is not None:
                questions.append(normalize_question(raw))
        except LearningError as exc:
            errors.append(f"Frage {number}: {exc}")
    return questions, errors


def export_gift(questions: list[dict]) -> tuple[str, list[str]]:
    """Fragen → GIFT-Text. Zweite Rückgabe: Hinweise zu Fragen, die GIFT nicht ausdrücken kann."""
    chunks: list[str] = []
    skipped: list[str] = []
    for index, q in enumerate(questions, start=1):
        title = _escape(q.get("category") or f"Frage {index}")
        text = _escape(q["text"])
        kind = q["type"]
        if kind == "single":
            body = "\n".join(("=" if o["correct"] else "~") + _escape(o["text"])
                             + (f" #{_escape(o['feedback'])}" if o.get("feedback") else "") for o in q["options"])
        elif kind == "multi":
            right = sum(1 for o in q["options"] if o["correct"])
            good = f"{100 / right:.5f}".rstrip("0").rstrip(".")
            body = "\n".join(("~%" + (good if o["correct"] else "-100") + "%") + _escape(o["text"])
                             + (f" #{_escape(o['feedback'])}" if o.get("feedback") else "") for o in q["options"])
        elif kind == "truefalse":
            body = "TRUE" if q["correct"] else "FALSE"
        elif kind == "cloze":
            if len(q["gaps"]) != 1:
                skipped.append(f"Frage {index}: Lückentext mit mehreren Lücken lässt sich in GIFT nicht ausdrücken")
                continue
            before, _sep, after = re.split(r"(_{3,})", q["text"], maxsplit=1)
            text = _escape(before.rstrip()) + " {" + " ".join("=" + _escape(a) for a in q["gaps"][0]) + "} " \
                + _escape(after.lstrip())
            chunks.append(f"::{title}::{text.strip()}")
            continue
        elif kind == "matching":
            body = "\n".join(f"={_escape(p['left'])} -> {_escape(p['right'])}" for p in q["pairs"])
        else:
            body = f"#{q['value']:g}:{q.get('tolerance', 0):g}"
        chunks.append(f"::{title}::{text} {{\n{body}\n}}" if "\n" in body else f"::{title}::{text} {{{body}}}")
    return "\n\n".join(chunks) + ("\n" if chunks else ""), skipped


# ----------------------------------------------------------------------------- Umfrage
SURVEY_FIELD_TYPES = ("select", "multiselect", "scale", "yesno", "textarea", "text", "number")


def aggregate_survey(fields: list[dict], responses: list[dict]) -> list[dict]:
    """Auswertung je Frage aus den (bereits geprüften) Antworten ``[{feld: wert}]``."""
    out = []
    for f in fields:
        fid, ftype = f["id"], f["type"]
        values = [r.get(fid) for r in responses]
        item: dict[str, Any] = {"id": fid, "type": ftype, "label": f["label"]}
        given = [v for v in values if v not in (None, "", [])]
        item["answered"] = len(given)
        if ftype in ("select", "multiselect"):
            counts = {o: 0 for o in f.get("options", [])}
            for v in given:
                for o in (v if isinstance(v, list) else [v]):
                    if o in counts:
                        counts[o] += 1
            item["counts"] = [{"option": o, "count": n} for o, n in counts.items()]
        elif ftype == "yesno":
            item["counts"] = [{"option": "Ja", "count": sum(1 for v in given if v is True)},
                              {"option": "Nein", "count": sum(1 for v in given if v is False)}]
            item["answered"] = sum(1 for v in values if isinstance(v, bool))
        elif ftype == "scale":
            nums = [int(v) for v in given if isinstance(v, (int, float))]
            item["counts"] = [{"option": str(n), "count": nums.count(n)} for n in range(1, 6)]
            item["mean"] = round(sum(nums) / len(nums), 2) if nums else None
            item["answered"] = len(nums)
        elif ftype == "number":
            nums = [float(v) for v in given if isinstance(v, (int, float)) and not isinstance(v, bool)]
            item["mean"] = round(sum(nums) / len(nums), 2) if nums else None
            item["min"] = min(nums) if nums else None
            item["max"] = max(nums) if nums else None
            item["answered"] = len(nums)
        else:
            item["texts"] = [str(v) for v in given]
        out.append(item)
    return out
