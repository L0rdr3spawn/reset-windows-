"""Formular-Baukasten – reine Logik ohne Datenbank (Doku: docs/FORMULARE.md).

* :func:`normalize_definition` prüft und bereinigt die Beschreibung eines Formulars (Felder, Zielgruppe, Ablauf,
  Fristen, Aktionen) – was ein Browser schickt, wird nie ungeprüft gespeichert.
* :func:`clean_answers` prüft die Antworten einer Einreichung gegen genau diese Fassung.
* :data:`LIBRARY` – fertige Vorlagen für Schulen (Beurlaubung, Entschuldigung, Einverständnisse …).
* :func:`csv_cell` schützt CSV-Exporte vor Formel-Einschleusung.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Optional

from .branding import PRODUCT_NAME

FIELD_TYPES: dict[str, str] = {
    "text": "Text (kurz)", "textarea": "Text (lang)", "number": "Zahl", "date": "Datum",
    "daterange": "Zeitraum von–bis", "select": "Auswahl", "multiselect": "Mehrfachauswahl", "yesno": "Ja/Nein",
    "confirm": "Ich bestätige (Häkchen)", "signature": "Unterschrift (Name + Datum)", "file": "Datei-Upload",
    "student": "Schüler/in (Kind)", "periods": "Stundenauswahl", "scale": "Skala 1–5",
}
CATEGORIES: dict[str, str] = {
    "beurlaubung": "Beurlaubung", "krankmeldung": "Krankmeldung / Entschuldigung",
    "einverstaendnis": "Einverständnis / Einwilligung", "antrag": "Antrag", "rueckmeldung": "Rückmeldung",
    "sonstiges": "Sonstiges",
}
AUDIENCE_ROLES: dict[str, str] = {
    "eltern": "Eltern", "schueler_adult": "Volljährige Schüler/innen", "schueler": "Schüler/innen",
    "lehrer": "Lehrkräfte", "sekretariat": "Sekretariat", "schulleitung": "Schulleitung",
}
APPROVERS: dict[str, str] = {
    "class_teacher": "Klassenleitung des Kindes", "sekretariat": "Sekretariat", "schulleitung": "Schulleitung",
    "user": "Bestimmte Person",
}
ACTION_TYPES: dict[str, str] = {
    "create_absence": "Beurlaubung/Krankmeldung anlegen", "inform_teachers": "Lehrkräfte der Stunden informieren",
    "calendar_entry": "Termin in den Schulkalender eintragen",
}
ABSENCE_KINDS = ("beurlaubung", "krank", "fehlt")
STATUS_LABELS: dict[str, str] = {
    "eingereicht": "eingereicht", "in_pruefung": "in Prüfung", "genehmigt": "genehmigt", "abgelehnt": "abgelehnt",
    "erledigt": "erledigt", "zurueckgezogen": "zurückgezogen",
}
OPEN_STATUSES = ("eingereicht", "in_pruefung")
FINAL_STATUSES = ("genehmigt", "abgelehnt", "erledigt", "zurueckgezogen")
TEMPLATE_STATUSES = ("entwurf", "aktiv", "archiviert")

MAX_FIELDS = 40
MAX_STEPS = 4
MAX_OPTIONS = 30
MAX_FILES = 5
MAX_TEXT = 200
MAX_LONG_TEXT = 4000
MAX_RANGE_DAYS = 366
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,29}$")
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class FormError(ValueError):
    """Ungültige Formularbeschreibung oder ungültige Antworten (Text ist für Nutzer/innen gedacht)."""


# ----------------------------------------------------------------------------- Hilfen
def clean_text(value: Any, limit: int, *, multiline: bool = False) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch == "\n" or ch >= " ") if multiline else " ".join(text.split())
    return text.strip()[:limit]


def _iso(value: Any, label: str) -> date:
    if not isinstance(value, str) or not _ISO_RE.match(value):
        raise FormError(f"{label}: bitte ein Datum angeben")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise FormError(f"{label}: ungültiges Datum") from None


def _opt_date(value: Any, label: str) -> Optional[str]:
    if value in (None, ""):
        return None
    return _iso(value, label).isoformat()


def _opt_int(value: Any, label: str, low: int, high: int) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise FormError(f"{label}: bitte eine ganze Zahl angeben") from None
    if not low <= number <= high:
        raise FormError(f"{label}: erlaubt sind {low} bis {high}")
    return number


def csv_cell(value: Any) -> str:
    """CSV-Zelle ohne Formel-Einschleusung (``=``, ``+``, ``-``, ``@``, Tab am Anfang werden entschärft)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


# ----------------------------------------------------------------------------- Felder
def _normalize_field(raw: Any, index: int, used: set[str]) -> dict:
    if not isinstance(raw, dict):
        raise FormError("Ungültiges Feld")
    ftype = str(raw.get("type") or "")
    if ftype not in FIELD_TYPES:
        raise FormError(f"Feld {index + 1}: unbekannte Art „{ftype}“")
    label = clean_text(raw.get("label"), 200)
    if not label:
        raise FormError(f"Feld {index + 1}: bitte eine Beschriftung eingeben")
    fid = str(raw.get("id") or "").strip().lower()
    if not fid:
        fid = f"f{index + 1}"
        while fid in used:
            fid += "x"
    if not _ID_RE.match(fid):
        raise FormError(f"Feld „{label}“: ungültige Kennung")
    if fid in used:
        raise FormError(f"Feld „{label}“: Kennung „{fid}“ kommt doppelt vor")
    used.add(fid)
    field: dict[str, Any] = {"id": fid, "type": ftype, "label": label,
                             "help": clean_text(raw.get("help"), 500, multiline=True),
                             "required": bool(raw.get("required"))}
    if ftype in ("select", "multiselect"):
        options = [clean_text(o, 80) for o in (raw.get("options") or []) if clean_text(o, 80)]
        options = list(dict.fromkeys(options))
        if not options:
            raise FormError(f"Feld „{label}“: bitte mindestens eine Auswahlmöglichkeit angeben")
        if len(options) > MAX_OPTIONS:
            raise FormError(f"Feld „{label}“: höchstens {MAX_OPTIONS} Auswahlmöglichkeiten")
        field["options"] = options
    if ftype == "scale":
        # feste Skala 1–5; optionale Beschriftung der Enden („trifft nicht zu“ … „trifft voll zu“)
        field["low"] = clean_text(raw.get("low"), 40)
        field["high"] = clean_text(raw.get("high"), 40)
    if ftype == "number":
        for key in ("min", "max"):
            if raw.get(key) not in (None, ""):
                try:
                    field[key] = float(raw[key])
                except (TypeError, ValueError):
                    raise FormError(f"Feld „{label}“: {key} muss eine Zahl sein") from None
    if ftype in ("text", "textarea"):
        field["max"] = _opt_int(raw.get("max"), f"Feld „{label}“", 1, MAX_LONG_TEXT if ftype == "textarea" else 500) \
            or (MAX_LONG_TEXT if ftype == "textarea" else MAX_TEXT)
    if ftype == "confirm":
        field["text"] = clean_text(raw.get("text"), 500, multiline=True)
    if ftype == "student":
        field["required"] = True
    elif ftype in ("confirm", "signature"):
        field["required"] = bool(raw.get("required", True))
    return field


def _normalize_audience(raw: Any) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    roles = [r for r in dict.fromkeys(raw.get("roles") or []) if r in AUDIENCE_ROLES]
    if not roles:
        raise FormError("Bitte festlegen, wer das Formular ausfüllen darf")
    scope = raw.get("scope") if raw.get("scope") in ("all", "classes", "grades") else "all"
    classes = [clean_text(c, 40) for c in (raw.get("classes") or []) if clean_text(c, 40)][:200]
    grades: list[int] = []
    for g in raw.get("grades") or []:
        try:
            grades.append(int(g))
        except (TypeError, ValueError):
            continue
    grades = sorted({g for g in grades if 0 <= g <= 20})
    if scope == "classes" and not classes:
        raise FormError("Bitte mindestens eine Klasse auswählen oder „Alle“ wählen")
    if scope == "grades" and not grades:
        raise FormError("Bitte mindestens einen Jahrgang auswählen oder „Alle“ wählen")
    return {"roles": roles, "scope": scope, "classes": classes if scope == "classes" else [],
            "grades": grades if scope == "grades" else []}


def _normalize_workflow(raw: Any) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    steps = []
    for index, s in enumerate((raw.get("steps") or [])[:MAX_STEPS + 1]):
        if not isinstance(s, dict) or s.get("approver") not in APPROVERS:
            raise FormError(f"Schritt {index + 1}: bitte angeben, wer prüft")
        step: dict[str, Any] = {"approver": s["approver"],
                                "label": clean_text(s.get("label"), 80) or APPROVERS[s["approver"]]}
        if s["approver"] == "user":
            try:
                step["user_id"] = int(s.get("user_id"))
            except (TypeError, ValueError):
                raise FormError(f"Schritt {index + 1}: bitte die Person auswählen") from None
        steps.append(step)
    if len(steps) > MAX_STEPS:
        raise FormError(f"Höchstens {MAX_STEPS} Prüfschritte")
    return {"steps": steps, "auto_complete": bool(raw.get("auto_complete")) and not steps}


def _normalize_deadline(raw: Any) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    out = {"open_from": _opt_date(raw.get("open_from"), "Frist „ab“"),
           "open_until": _opt_date(raw.get("open_until"), "Frist „bis“"),
           "decide_days": _opt_int(raw.get("decide_days"), "Bearbeitungsfrist (Tage)", 1, 90),
           "remind_days": _opt_int(raw.get("remind_days"), "Erinnerung (Tage)", 1, 60)}
    if out["open_from"] and out["open_until"] and out["open_until"] < out["open_from"]:
        raise FormError("Die Frist endet vor ihrem Beginn")
    return out


def _normalize_actions(raw: Any, fields: dict[str, dict]) -> list[dict]:
    out: list[dict] = []

    def need(fid: Any, types: tuple[str, ...], label: str, required: bool = True) -> Optional[str]:
        if not fid:
            if required:
                raise FormError(f"Aktion: bitte das Feld für „{label}“ wählen")
            return None
        field = fields.get(str(fid))
        if field is None or field["type"] not in types:
            raise FormError(f"Aktion: Feld für „{label}“ passt nicht (benötigt: "
                            f"{', '.join(FIELD_TYPES[t] for t in types)})")
        return field["id"]

    for item in (raw or [])[:6]:
        if not isinstance(item, dict) or item.get("type") not in ACTION_TYPES:
            raise FormError("Unbekannte Aktion")
        kind = item["type"]
        if kind == "create_absence":
            if item.get("kind") not in ABSENCE_KINDS:
                raise FormError("Aktion „Beurlaubung/Krankmeldung anlegen“: bitte die Art wählen")
            status = item.get("status") if item.get("status") in ("gemeldet", "entschuldigt") else "entschuldigt"
            out.append({"type": kind, "kind": item["kind"], "status": status,
                        "student": need(item.get("student"), ("student",), "Schüler/in", required=False),
                        "range": need(item.get("range"), ("daterange", "date"), "Zeitraum"),
                        "periods": need(item.get("periods"), ("periods",), "Stunden", required=False),
                        "reason": need(item.get("reason"), ("text", "textarea", "select"), "Anlass/Grund",
                                       required=False)})
        elif kind == "calendar_entry":
            title = clean_text(item.get("title"), 120)
            if not title:
                raise FormError("Aktion „Termin eintragen“: bitte einen Titel angeben (ohne persönliche Angaben)")
            out.append({"type": kind, "title": title,
                        "date": need(item.get("date"), ("date", "daterange"), "Termin")})
        else:
            out.append({"type": kind})
    return out


def normalize_fields(raw_fields: Any, *, allowed: Optional[tuple[str, ...]] = None, limit: int = MAX_FIELDS) -> list[dict]:
    """Nur die Felder prüfen und bereinigen (Umfragen im Kursraum nutzen dieselben Feldarten wie Formulare).
    ``allowed`` schränkt die Feldarten ein."""
    if not isinstance(raw_fields, list) or not raw_fields:
        raise FormError("Bitte mindestens eine Frage hinzufügen")
    if len(raw_fields) > limit:
        raise FormError(f"Höchstens {limit} Fragen")
    used: set[str] = set()
    fields = [_normalize_field(f, i, used) for i, f in enumerate(raw_fields)]
    if allowed is not None:
        bad = next((f for f in fields if f["type"] not in allowed), None)
        if bad is not None:
            raise FormError(f"Frage „{bad['label']}“: die Art „{FIELD_TYPES[bad['type']]}“ ist hier nicht erlaubt")
    return fields


def normalize_definition(raw: Any, *, template_title: str = "") -> dict:
    """Prüft und bereinigt die Beschreibung eines Formulars (``FormError`` mit deutschem Text bei Fehlern)."""
    if not isinstance(raw, dict):
        raise FormError("Ungültige Formularbeschreibung")
    raw_fields = raw.get("fields")
    if not isinstance(raw_fields, list) or not raw_fields:
        raise FormError("Bitte mindestens ein Feld hinzufügen")
    if len(raw_fields) > MAX_FIELDS:
        raise FormError(f"Höchstens {MAX_FIELDS} Felder")
    used: set[str] = set()
    fields = [_normalize_field(f, i, used) for i, f in enumerate(raw_fields)]
    if sum(1 for f in fields if f["type"] == "student") > 1:
        raise FormError("Höchstens ein Feld „Schüler/in“")
    by_id = {f["id"]: f for f in fields}
    defn = {
        "fields": fields,
        "audience": _normalize_audience(raw.get("audience")),
        "workflow": _normalize_workflow(raw.get("workflow")),
        "deadline": _normalize_deadline(raw.get("deadline")),
        "actions": _normalize_actions(raw.get("actions"), by_id),
        "once": bool(raw.get("once")),
        "notify": {"submitter": not (isinstance(raw.get("notify"), dict) and raw["notify"].get("submitter") is False)},
        "legacy_pdf": raw.get("legacy_pdf") if raw.get("legacy_pdf") in ("leave-form", "excuse-form") else None,
        "intro": clean_text(raw.get("intro"), 1500, multiline=True),
    }
    if any(a["type"] == "create_absence" for a in defn["actions"]) and "student" not in {f["type"] for f in fields}:
        raise FormError("Die Aktion „Beurlaubung/Krankmeldung anlegen“ braucht ein Feld „Schüler/in“")
    if any(a["type"] in ("create_absence", "calendar_entry") for a in defn["actions"]) \
            and not (defn["workflow"]["steps"] or defn["workflow"]["auto_complete"]):
        raise FormError("Aktionen laufen bei Genehmigung: bitte mindestens einen Prüfschritt festlegen "
                        "(oder „Sofort erledigt“ wählen)")
    return defn


def has_student_field(defn: dict) -> bool:
    return any(f["type"] == "student" for f in defn.get("fields", []))


def field_by_id(defn: dict, fid: Optional[str]) -> Optional[dict]:
    return next((f for f in defn.get("fields", []) if f["id"] == fid), None)


# ----------------------------------------------------------------------------- Antworten
def _empty(value: Any) -> bool:
    return value in (None, "", [], {}) or (isinstance(value, dict) and not any(value.values()))


def clean_answers(defn: dict, answers: Any, *, student_id: Optional[str], periods: int, today: date,
                  signer: str = "") -> dict[str, Any]:
    """Antworten prüfen und bereinigen. ``student_id`` füllt das Feld „Schüler/in“ (vom Server geprüft), ``today``
    setzt das Datum der Unterschrift, ``periods`` = Stunden pro Tag der Schule."""
    answers = answers if isinstance(answers, dict) else {}
    out: dict[str, Any] = {}
    for f in defn["fields"]:
        fid, ftype, label = f["id"], f["type"], f["label"]
        value = answers.get(fid)
        required = f.get("required", False)

        def missing(label: str = label) -> FormError:
            return FormError(f"Bitte ausfüllen: {label}")

        if ftype == "student":
            if not student_id:
                raise FormError("Bitte die Schülerin / den Schüler auswählen")
            out[fid] = student_id
        elif ftype in ("text", "textarea"):
            text = clean_text(value, f.get("max") or MAX_TEXT, multiline=ftype == "textarea")
            if required and not text:
                raise missing()
            out[fid] = text
        elif ftype == "number":
            if _empty(value):
                if required:
                    raise missing()
                out[fid] = None
                continue
            try:
                number = float(str(value).replace(",", "."))
            except ValueError:
                raise FormError(f"{label}: bitte eine Zahl eingeben") from None
            if number != number or number in (float("inf"), float("-inf")):
                raise FormError(f"{label}: bitte eine Zahl eingeben")
            if "min" in f and number < f["min"] or "max" in f and number > f["max"]:
                raise FormError(f"{label}: der Wert liegt außerhalb des erlaubten Bereichs")
            out[fid] = int(number) if number == int(number) else number
        elif ftype == "date":
            if _empty(value):
                if required:
                    raise missing()
                out[fid] = ""
                continue
            out[fid] = _iso(value, label).isoformat()
        elif ftype == "daterange":
            if _empty(value):
                if required:
                    raise missing()
                out[fid] = {"from": "", "to": ""}
                continue
            if not isinstance(value, dict):
                raise FormError(f"{label}: bitte Beginn und Ende angeben")
            d1 = _iso(value.get("from"), f"{label} (von)")
            d2 = _iso(value.get("to") or value.get("from"), f"{label} (bis)")
            if d2 < d1:
                raise FormError(f"{label}: das Ende liegt vor dem Beginn")
            if (d2 - d1).days >= MAX_RANGE_DAYS:
                raise FormError(f"{label}: der Zeitraum ist zu lang")
            out[fid] = {"from": d1.isoformat(), "to": d2.isoformat()}
        elif ftype == "select":
            text = clean_text(value, 80)
            if not text:
                if required:
                    raise missing()
                out[fid] = ""
            elif text not in f["options"]:
                raise FormError(f"{label}: bitte eine der Möglichkeiten wählen")
            else:
                out[fid] = text
        elif ftype == "multiselect":
            chosen = [clean_text(v, 80) for v in (value if isinstance(value, list) else [])]
            chosen = [c for c in dict.fromkeys(chosen) if c]
            if any(c not in f["options"] for c in chosen):
                raise FormError(f"{label}: bitte nur die angebotenen Möglichkeiten wählen")
            if required and not chosen:
                raise missing()
            out[fid] = chosen
        elif ftype == "scale":
            if _empty(value):
                if required:
                    raise missing()
                out[fid] = None
                continue
            try:
                step = int(str(value).strip())
            except ValueError:
                raise FormError(f"{label}: bitte einen Wert von 1 bis 5 wählen") from None
            if not 1 <= step <= 5:
                raise FormError(f"{label}: bitte einen Wert von 1 bis 5 wählen")
            out[fid] = step
        elif ftype == "yesno":
            if value in (None, ""):
                if required:
                    raise missing()
                out[fid] = None
            elif isinstance(value, bool):
                out[fid] = value
            elif str(value).lower() in ("ja", "true", "1"):
                out[fid] = True
            elif str(value).lower() in ("nein", "false", "0"):
                out[fid] = False
            else:
                raise FormError(f"{label}: bitte „Ja“ oder „Nein“ wählen")
        elif ftype == "confirm":
            ok = value is True or str(value).lower() in ("true", "1", "ja")
            if required and not ok:
                raise FormError(f"Bitte bestätigen: {label}")
            out[fid] = ok
        elif ftype == "signature":
            name = clean_text(value.get("name") if isinstance(value, dict) else value, 120)
            if not name:
                if required:
                    raise FormError(f"Bitte mit vollem Namen unterschreiben: {label}")
                out[fid] = None
            else:
                out[fid] = {"name": name, "date": today.isoformat(), "by": clean_text(signer, 120)}
        elif ftype == "file":
            ids = [str(v) for v in (value if isinstance(value, list) else []) if isinstance(v, str)]
            ids = list(dict.fromkeys(ids))
            if len(ids) > MAX_FILES:
                raise FormError(f"{label}: höchstens {MAX_FILES} Dateien")
            if required and not ids:
                raise missing()
            out[fid] = ids
        elif ftype == "periods":
            raw_periods = value if isinstance(value, list) else []
            nums: list[int] = []
            for p in raw_periods:
                try:
                    nums.append(int(p))
                except (TypeError, ValueError):
                    raise FormError(f"{label}: ungültige Stunde") from None
            if any(not 0 <= p < max(periods, 1) for p in nums):
                raise FormError(f"{label}: ungültige Stunde")
            if required and not nums:
                raise missing()
            out[fid] = sorted(set(nums))
    return out


def display_value(field: dict, value: Any) -> str:
    """Antwort als Text (PDF, CSV, Listen)."""
    ftype = field["type"]
    if value in (None, "", []):
        return ""
    if ftype == "yesno":
        return "Ja" if value else "Nein"
    if ftype == "scale":
        return f"{value} von 5"
    if ftype == "confirm":
        return "Ja, bestätigt" if value else "Nein"
    if ftype == "daterange" and isinstance(value, dict):
        d1, d2 = value.get("from") or "", value.get("to") or ""
        return fmt_date(d1) if d1 == d2 else f"{fmt_date(d1)} bis {fmt_date(d2)}"
    if ftype == "date":
        return fmt_date(str(value))
    if ftype == "multiselect":
        return ", ".join(value)
    if ftype == "signature" and isinstance(value, dict):
        return f"{value.get('name', '')}, {fmt_date(value.get('date') or '')}"
    if ftype == "periods":
        return ", ".join(f"{int(p) + 1}." for p in value) + " Stunde"
    if ftype == "file":
        return f"{len(value)} Datei(en)"
    return str(value)


def fmt_date(iso_day: str) -> str:
    try:
        return date.fromisoformat(iso_day).strftime("%d.%m.%Y")
    except ValueError:
        return iso_day


# ----------------------------------------------------------------------------- Zielgruppe / Fristen
def in_window(defn: dict, today: date) -> bool:
    """Ist das Formular heute zum Ausfüllen offen (Frist „ab“/„bis“)?"""
    dl = defn.get("deadline") or {}
    if dl.get("open_from") and today.isoformat() < dl["open_from"]:
        return False
    return not (dl.get("open_until") and today.isoformat() > dl["open_until"])


def class_in_target(defn: dict, class_id: Optional[str], grade: Optional[int]) -> bool:
    aud = defn.get("audience") or {}
    scope = aud.get("scope", "all")
    if scope == "all":
        return True
    if scope == "classes":
        return class_id in (aud.get("classes") or [])
    return grade is not None and grade in (aud.get("grades") or [])


def due_date(defn: dict, created: date) -> Optional[str]:
    days = (defn.get("deadline") or {}).get("decide_days")
    return (created + timedelta(days=days)).isoformat() if days else None


# ----------------------------------------------------------------------------- Bibliothek
def _f(fid: str, ftype: str, label: str, **extra: Any) -> dict:
    return {"id": fid, "type": ftype, "label": label, **extra}


def _lib(key: str, title: str, description: str, category: str, fields: list[dict], *, sensitive: bool = False,
         roles: tuple[str, ...] = ("eltern", "schueler_adult"), steps: tuple[str, ...] = (), auto: bool = False,
         actions: Optional[list[dict]] = None, once: bool = False, legacy: Optional[str] = None,
         intro: str = "", decide_days: Optional[int] = None) -> dict:
    return {"key": key, "title": title, "description": description, "category": category, "sensitive": sensitive,
            "definition": {
                "fields": fields, "intro": intro, "legacy_pdf": legacy, "once": once,
                "audience": {"roles": list(roles), "scope": "all", "classes": [], "grades": []},
                "workflow": {"steps": [{"approver": s} for s in steps], "auto_complete": auto},
                "deadline": {"open_from": None, "open_until": None, "decide_days": decide_days, "remind_days": None},
                "actions": actions or [], "notify": {"submitter": True}}}


LIBRARY: list[dict] = [
    _lib("beurlaubung", "Antrag auf Beurlaubung",
         "Beurlaubung vom Unterricht (Arzt-, Behördentermin …). Bei Genehmigung wird die Beurlaubung im "
         f"{PRODUCT_NAME} angelegt und die Lehrkräfte der betroffenen Stunden werden informiert.", "beurlaubung",
         [_f("kind", "student", "Schüler/in"), _f("zeitraum", "daterange", "Zeitraum", required=True),
          _f("stunden", "periods", "Nur einzelne Stunden (leer = ganze Tage)"),
          _f("anlass", "textarea", "Anlass der Beurlaubung", required=True, max=500,
             help="z. B. Arzttermin, Behördentermin, Fahrprüfung – Angaben zur Gesundheit sind nicht nötig."),
          _f("sig", "signature", "Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in")],
         steps=("class_teacher",), legacy="leave-form", decide_days=3,
         actions=[{"type": "create_absence", "kind": "beurlaubung", "status": "entschuldigt", "student": "kind",
                   "range": "zeitraum", "periods": "stunden", "reason": "anlass"}, {"type": "inform_teachers"}]),
    _lib("entschuldigung", "Schriftliche Entschuldigung",
         "Entschuldigung für versäumten Unterricht. Die Klassenleitung bestätigt; danach steht die Fehlzeit als "
         f"entschuldigt im {PRODUCT_NAME}.", "krankmeldung",
         [_f("kind", "student", "Schüler/in"), _f("zeitraum", "daterange", "Gefehlt vom – bis", required=True),
          _f("stunden", "periods", "Nur einzelne Stunden (leer = ganze Tage)"),
          _f("grund", "textarea", "Grund (freiwillig – Angaben zur Gesundheit sind nicht nötig)", max=500),
          _f("attest", "yesno", "Ein ärztliches Attest liegt bei"),
          _f("beleg", "file", "Attest / Foto der unterschriebenen Entschuldigung"),
          _f("sig", "signature", "Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in")],
         sensitive=True, steps=("class_teacher",), legacy="excuse-form", decide_days=5,
         actions=[{"type": "create_absence", "kind": "krank", "status": "entschuldigt", "student": "kind",
                   "range": "zeitraum", "periods": "stunden", "reason": "grund"}]),
    _lib("klassenfahrt", "Einverständnis Klassenfahrt",
         "Teilnahme, Gesundheitshinweise und Notfallnummer für eine Klassenfahrt.", "einverstaendnis",
         [_f("kind", "student", "Schüler/in"),
          _f("teilnahme", "yesno", "Mein Kind nimmt an der Fahrt teil", required=True),
          _f("schwimmen", "yesno", "Mein Kind darf unter Aufsicht baden/schwimmen"),
          _f("gesundheit", "textarea", "Allergien, Medikamente, Hinweise (freiwillig)", max=800),
          _f("notfall", "text", "Notfallnummer während der Fahrt", required=True),
          _f("ok", "confirm", "Bestätigung", text="Ich habe die Informationen zur Fahrt gelesen und bin einverstanden."),
          _f("sig", "signature", "Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in")],
         sensitive=True, once=True),
    _lib("foto", "Foto- und Medien-Einwilligung",
         "Einwilligung zur Veröffentlichung von Fotos und Videos (jederzeit widerrufbar).", "einverstaendnis",
         [_f("kind", "student", "Schüler/in"),
          _f("nutzung", "multiselect", "Fotos/Videos dürfen verwendet werden für",
             options=["Schulinterne Dokumentation", "Schulwebsite", "Jahrbuch", "Presse / Zeitung", "Soziale Medien"]),
          _f("ok", "confirm", "Bestätigung",
             text="Die Einwilligung ist freiwillig und kann jederzeit für die Zukunft widerrufen werden."),
          _f("sig", "signature", "Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in")],
         once=True, auto=True),
    _lib("elternabend", "Rückmeldung Elternabend",
         "Anmeldung/Rückmeldung zum Elternabend.", "rueckmeldung",
         [_f("kind", "student", "Schüler/in"),
          _f("teilnahme", "select", "Ich komme", required=True,
             options=["Ja, ein Elternteil", "Ja, beide Elternteile", "Nein, ich kann nicht"]),
          _f("anmerkung", "textarea", "Anmerkung / Themenwunsch", max=500)],
         roles=("eltern",), once=True, auto=True),
    _lib("nachteilsausgleich", "Antrag Nachteilsausgleich",
         "Antrag auf Nachteilsausgleich (Förderbedarf, Teilleistungsstörung, Erkrankung). Prüfung durch Klassenleitung "
         "und Schulleitung; Angaben sind besonders geschützt.", "antrag",
         [_f("kind", "student", "Schüler/in"),
          _f("art", "multiselect", "Gewünschter Ausgleich",
             options=["Zeitzuschlag", "Pausen", "Eigener Raum", "Technische Hilfsmittel", "Anderes"]),
          _f("begruendung", "textarea", "Begründung", required=True, max=1500,
             help="Nur so viel, wie für die Entscheidung nötig ist."),
          _f("nachweis", "file", "Nachweis (Gutachten, Attest)"),
          _f("sig", "signature", "Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in")],
         sensitive=True, steps=("class_teacher", "schulleitung"), decide_days=14),
    _lib("schulbescheinigung", "Schulbescheinigung anfordern",
         "Bescheinigung über den Schulbesuch (z. B. Kindergeld, Ausbildung, Behörde).", "antrag",
         [_f("kind", "student", "Schüler/in"),
          _f("art", "select", "Art der Bescheinigung", required=True,
             options=["Schulbesuchsbescheinigung", "Bescheinigung für Kindergeld", "Bescheinigung für BAföG",
                      "Sonstige"]),
          _f("zweck", "text", "Verwendungszweck", required=True),
          _f("anzahl", "number", "Anzahl", min=1, max=10),
          _f("bis", "date", "Benötigt bis")],
         roles=("eltern", "schueler_adult"), steps=("sekretariat",), decide_days=5),
]


def library_entry(key: str) -> Optional[dict]:
    return next((e for e in LIBRARY if e["key"] == key), None)
