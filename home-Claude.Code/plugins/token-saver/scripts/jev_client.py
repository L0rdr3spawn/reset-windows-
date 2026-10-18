"""Minimaler Client für TypeSafe Jev (System One), nur Standardbibliothek.

Umgebungsvariablen:
  JEV_API_KEY   – Pflicht; ohne Key ist Jev aus.
  JEV_BASE_URL  – Standard https://api.typesafe.ai/v1/systemone
  JEV_MODEL     – Standard jev-latest

Das Antwortformat ist nur aus Sekundärquellen bekannt, daher liest `parse_*`
mehrere plausible Formen tolerant aus und liefert im Zweifel None.
"""
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_URL = "https://api.typesafe.ai/v1/systemone"
MAX_STATE_CHARS = 24000  # Kontextfenster ~32k Tokens, großzügig darunter bleiben


class JevError(Exception):
    pass


def api_key():
    return os.environ.get("JEV_API_KEY") or None


def noul(question, true_desc, false_desc):
    return {"type": "noul", "question": question, "criteria": {"true": true_desc, "false": false_desc}}


def choice(question, options):
    """options: {name: Beschreibung}. Enthält immer eine Ausweich-Option."""
    opts = dict(options)
    opts.setdefault("unclear", "None of the other options clearly fits")
    return {"type": "choice", "question": question, "criteria": opts}


def build_request(state, questions, model=None):
    if isinstance(state, str) and len(state) > MAX_STATE_CHARS:
        state = state[:MAX_STATE_CHARS] + "\n…[truncated]"
    return {
        "model": model or os.environ.get("JEV_MODEL") or "jev-latest",
        "state": state if state is not None else "",
        "questions": questions,
    }


def ask(state, questions, timeout=1.5, key=None):
    """Schickt eine Anfrage; gibt (antworten_dict, latenz_ms) zurück oder wirft JevError."""
    key = key or api_key()
    if not key:
        raise JevError("JEV_API_KEY not set")
    body = json.dumps(build_request(state, questions)).encode("utf-8")
    req = urllib.request.Request(
        os.environ.get("JEV_BASE_URL") or DEFAULT_URL,
        data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise JevError("HTTP %d: %s" % (exc.code, detail))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise JevError(str(exc))
    latency = (time.monotonic() - start) * 1000
    return answers_of(payload), latency


# ------------------------------------------------------------ tolerantes Parsen

def answers_of(payload):
    """Findet das Dict {frage_name: antwort} in der Antwort."""
    if not isinstance(payload, dict):
        return {}
    for key in ("answers", "results", "decisions", "outputs", "data"):
        inner = payload.get(key)
        if isinstance(inner, dict):
            return inner
        if isinstance(inner, list):  # [{"name": ..., ...}]
            return {a.get("name") or a.get("id"): a for a in inner if isinstance(a, dict)}
    return payload


def _num(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def parse_noul(answer):
    """Wahrscheinlichkeit für `true` (0..1) oder None."""
    if isinstance(answer, bool):
        return 1.0 if answer else 0.0
    if _num(answer) is not None:
        return _num(answer)
    if not isinstance(answer, dict):
        return None
    for key in ("probability", "p", "prob", "probability_true", "p_true"):
        if _num(answer.get(key)) is not None:
            return _num(answer[key])
    probs = answer.get("probabilities")
    if isinstance(probs, dict):
        for key in ("true", "True", "yes"):
            if _num(probs.get(key)) is not None:
                return _num(probs[key])
    value = answer.get("value", answer.get("answer", answer.get("choice")))
    if isinstance(value, str) and value.lower() in ("true", "false"):
        value = value.lower() == "true"
    if isinstance(value, bool):
        conf = _num(answer.get("confidence"))
        if conf is None:
            return 1.0 if value else 0.0
        return conf if value else 1.0 - conf
    return None


def parse_choice(answer):
    """(option, konfidenz) oder (None, None)."""
    if isinstance(answer, str):
        return answer, None
    if not isinstance(answer, dict):
        return None, None
    probs = answer.get("probabilities")
    option = answer.get("choice", answer.get("value", answer.get("answer")))
    conf = _num(answer.get("confidence"))
    if isinstance(probs, dict) and probs:
        best = max(probs, key=lambda k: probs[k] if _num(probs[k]) is not None else -1)
        option = option or best
        if conf is None:
            conf = _num(probs.get(option))
    return option, conf
