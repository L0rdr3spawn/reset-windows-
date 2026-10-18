"""Feiertage und Schulferien aus einer öffentlichen API automatisch übernehmen.

Quellen (kostenlos, ohne Schlüssel):

* **OpenHolidays API** (``openholidaysapi.org``): gesetzliche Feiertage *und* Schulferien je Land/Region
  (``/PublicHolidays``, ``/SchoolHolidays``, ``/Countries``, ``/Subdivisions``; DE: Bundesländer ``DE-BY`` …).
* **Nager.Date** (``date.nager.at``): Rückfall für Länder, die OpenHolidays nicht kennt – nur gesetzliche Feiertage.

Einstellungen stehen im Schuldokument (``School.holiday_import``): ``enabled``, ``country`` (ISO), ``region``
(Code, leer = nur landesweite Einträge), ``language`` (Namen), ``seen`` (bereits übernommene Quell-IDs).

Regeln für das Übernehmen (:func:`plan_changes`):

* Importierte Einträge tragen ``Holiday.source`` (Quell-ID) und ``source_sig`` (Fingerabdruck der übernommenen Werte).
* Ein erneuter Import **aktualisiert** nur Einträge, die seit dem Import nicht verändert wurden; wurde ein Eintrag
  von Hand geändert (Fingerabdruck passt nicht mehr), bleibt er unberührt. Von Hand gelöschte Einträge (Quell-ID in
  ``seen``, aber nicht mehr vorhanden) kommen nicht wieder. Von Hand angelegte Einträge werden nie verändert oder
  gelöscht; gibt es schon einen von Hand angelegten Eintrag mit gleichem Zeitraum, wird nichts doppelt angelegt.
* Es wird nie gelöscht – auch nicht, was die Quelle später nicht mehr liefert.

Automatik (:func:`start`): Hintergrund-Thread prüft beim Start und danach täglich, ob das laufende und das nächste
Schuljahr übernommen sind (nur wenn ``enabled``). Fehler und fehlende Internetverbindung werden nur protokolliert
(nächster Versuch nach einer Stunde). Abschaltbar mit ``SM_HOLIDAY_IMPORT=0``.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from typing import Any, Optional

from . import net_guard
from .config import config

log = logging.getLogger("schulmanager.holiday_import")

OPENHOLIDAYS_URL = "https://openholidaysapi.org"
NAGER_URL = "https://date.nager.at/api/v3"
TIMEOUT = 10.0
CACHE_TTL = 24 * 3600
FIRST_DELAY = 30.0            # Sekunden nach dem Start
RETRY_AFTER_ERROR = 3600.0
INTERVAL = 24 * 3600.0

RE_COUNTRY = re.compile(r"^[A-Z]{2}$")
RE_REGION = re.compile(r"^[A-Z]{2}(-[A-Z0-9]{1,6}){0,2}$")
RE_LANG = re.compile(r"^[a-z]{2}$")


class HolidayImportError(RuntimeError):
    """Abruf oder Einstellung fehlgeschlagen (``status`` = HTTP-Status für die Route)."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


# ------------------------------------------------------------------ Netzwerk (in Tests ersetzt)
def fetch_json(url: str, params: Optional[dict] = None) -> Any:
    """GET → JSON mit Timeout. Fehler → :class:`HolidayImportError`."""
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Schulmanager"})
    try:
        with net_guard.urlopen(req, "https", timeout=TIMEOUT) as r:     # feste https-Adressen, trotzdem geprüft
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HolidayImportError(f"Der Ferien-Dienst antwortet mit Fehler {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise HolidayImportError("Der Ferien-Dienst ist nicht erreichbar (Internetverbindung prüfen).") from None
    except ValueError:
        raise HolidayImportError("Der Ferien-Dienst lieferte eine ungültige Antwort.") from None


_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()


def _cached(key: str, loader):
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    value = loader()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


# ------------------------------------------------------------------ Länder und Regionen
def _text(names: Any, lang: str) -> str:
    """Name aus ``[{"language": "DE", "text": …}]`` in der gewünschten Sprache (sonst DE, EN, erster)."""
    if isinstance(names, str):
        return names
    items = [n for n in (names or []) if isinstance(n, dict) and n.get("text")]
    for want in (lang.upper(), "DE", "EN"):
        for n in items:
            if str(n.get("language", "")).upper() == want:
                return str(n["text"])
    return str(items[0]["text"]) if items else ""


def countries(lang: str = "de") -> list[dict]:
    """``[{code, name, source}]`` – ``source`` = ``openholidays`` (mit Schulferien) oder ``nager`` (nur Feiertage)."""
    def load():
        oh = fetch_json(f"{OPENHOLIDAYS_URL}/Countries", {"languageIsoCode": lang.upper()})
        out = {c["isoCode"]: {"code": c["isoCode"], "name": _text(c.get("name"), lang), "source": "openholidays"}
               for c in oh if isinstance(c, dict) and c.get("isoCode")}
        try:
            for c in fetch_json(f"{NAGER_URL}/AvailableCountries"):
                code = c.get("countryCode")
                if code and code not in out:
                    out[code] = {"code": code, "name": c.get("name") or code, "source": "nager"}
        except HolidayImportError:
            log.info("Nager.Date-Länderliste nicht erreichbar – nur OpenHolidays")
        return sorted(out.values(), key=lambda c: c["name"].casefold())

    return _cached(f"countries:{lang}", load)


def _flatten(items: list, lang: str, parent: str = "") -> list[dict]:
    out = []
    for s in items or []:
        if not isinstance(s, dict) or not s.get("code"):
            continue
        out.append({"code": s["code"], "name": _text(s.get("name"), lang) or s.get("shortName") or s["code"],
                    "category": _text(s.get("category"), lang), "parent": parent})
        out += _flatten(s.get("children") or [], lang, s["code"])
    return out


def regions(country: str, lang: str = "de") -> list[dict]:
    """``[{code, name, category, parent}]`` (Bundesländer usw.); leer, wenn die Quelle keine Regionen kennt."""
    country = _check_country(country)
    src = next((c["source"] for c in countries(lang) if c["code"] == country), None)
    if src != "openholidays":
        return []
    items = _cached(f"regions:{country}:{lang}", lambda: fetch_json(
        f"{OPENHOLIDAYS_URL}/Subdivisions", {"countryIsoCode": country, "languageIsoCode": lang.upper()}))
    return sorted(_flatten(items, lang), key=lambda r: (r["parent"], r["name"].casefold()))


def _check_country(code: str) -> str:
    code = (code or "").strip().upper()
    if not RE_COUNTRY.match(code):
        raise HolidayImportError("Ungültiger Ländercode.", 422)
    return code


# ------------------------------------------------------------------ Einstellungen
DEFAULTS = {"enabled": False, "country": "DE", "region": "", "language": "de"}


def get_settings(school) -> dict:
    cur = dict(getattr(school, "holiday_import", None) or {})
    out = {**DEFAULTS, **{k: cur[k] for k in DEFAULTS if k in cur}}
    out["configured"] = bool(cur.get("country"))
    return out


def clean_settings(data: dict) -> dict:
    country = _check_country(data.get("country", ""))
    region = (data.get("region") or "").strip().upper()
    if region and (not RE_REGION.match(region) or not (region == country or region.startswith(country + "-"))):
        raise HolidayImportError("Ungültige Region.", 422)
    lang = (data.get("language") or "de").strip().lower()
    if not RE_LANG.match(lang):
        raise HolidayImportError("Ungültige Sprache.", 422)
    return {"enabled": bool(data.get("enabled")), "country": country, "region": region, "language": lang}


# ------------------------------------------------------------------ Abruf und Umwandlung
def school_year_of(day: date) -> int:
    """Startjahr des Schuljahres, in dem ``day`` liegt (Schuljahr: 1.8. – 31.7.)."""
    return day.year if day.month >= 8 else day.year - 1


def current_school_years(today: Optional[date] = None) -> list[int]:
    y = school_year_of(today or date.today())
    return [y, y + 1]


def _in_region(subdivisions: list, region: str) -> bool:
    """Gilt der Eintrag für die gewählte Region (gleicher Code oder übergeordnete Region)?"""
    for s in subdivisions or []:
        code = s.get("code", "") if isinstance(s, dict) else str(s)
        if region and (region == code or region.startswith(code + "-")):
            return True
    return False


def sig_of(name: str, date_from: str, date_to: str, kind: str) -> str:
    return hashlib.sha1(f"{name}|{date_from}|{date_to}|{kind}".encode()).hexdigest()[:12]


def _candidate(sid: str, name: str, d1: str, d2: str, kind: str) -> dict:
    return {"source": sid, "name": name.strip(), "date_from": d1, "date_to": d2, "kind": kind}


def _openholidays(country: str, region: str, lang: str, start: str, end: str) -> list[dict]:
    out: list[dict] = []
    params = {"countryIsoCode": country, "languageIsoCode": lang.upper(), "validFrom": start, "validTo": end,
              "subdivisionCode": region or None}
    for path, kind in (("PublicHolidays", "feiertag"), ("SchoolHolidays", "ferien")):
        data = fetch_json(f"{OPENHOLIDAYS_URL}/{path}", params)
        for h in data if isinstance(data, list) else []:
            if not isinstance(h, dict) or not h.get("id"):
                continue
            if kind == "feiertag" and h.get("type") not in (None, "Public"):
                continue
            if not (h.get("nationwide") or _in_region(h.get("subdivisions"), region)):
                continue                                          # andere Region / nur örtlich
            name = _text(h.get("name"), lang)
            d1, d2 = str(h.get("startDate", ""))[:10], str(h.get("endDate") or h.get("startDate", ""))[:10]
            if name and d1 and d2 and d2 >= d1 and d1 <= end and d2 >= start:
                one_day = kind == "ferien" and d1 == d2                 # z. B. Buß- und Bettag
                out.append(_candidate(f"oh:{h['id']}", name, d1, d2, "schulfrei" if one_day else kind))
    return out


def _nager(country: str, region: str, start: str, end: str) -> list[dict]:
    out: list[dict] = []
    for year in range(int(start[:4]), int(end[:4]) + 1):
        data = fetch_json(f"{NAGER_URL}/PublicHolidays/{year}/{country}")
        for h in data if isinstance(data, list) else []:
            d = str(h.get("date", ""))[:10]
            if not d or not start <= d <= end:
                continue
            if "Public" not in (h.get("types") or ["Public"]):
                continue
            if not (h.get("global", True) or (region and region in (h.get("counties") or []))):
                continue
            name = h.get("localName") or h.get("name") or ""
            sid = "nager:" + country + ":" + hashlib.sha1(f"{d}|{h.get('name', '')}".encode()).hexdigest()[:10]
            if name:
                out.append(_candidate(sid, name, d, d, "feiertag"))
    return out


def fetch_candidates(cfg: dict, years: list[int]) -> list[dict]:
    """Feiertage + Schulferien der Schuljahre ``years`` (Startjahre), nach Datum sortiert, ohne Doppelte."""
    country, region, lang = cfg["country"], cfg.get("region", ""), cfg.get("language", "de")
    src = next((c["source"] for c in countries(lang) if c["code"] == country), None)
    if src is None:
        raise HolidayImportError("Dieses Land wird vom Ferien-Dienst nicht unterstützt.", 422)
    found: dict[str, dict] = {}
    for y in sorted(set(years)):
        start, end = f"{y}-08-01", f"{y + 1}-07-31"
        items = _openholidays(country, region, lang, start, end) if src == "openholidays" \
            else _nager(country, region, start, end)
        for c in items:
            found.setdefault(c["source"], c)
    return sorted(found.values(), key=lambda c: (c["date_from"], c["date_to"], c["name"]))


# ------------------------------------------------------------------ Abgleich mit den Stammdaten
def plan_changes(school, candidates: list[dict]) -> list[dict]:
    """Was ein Import täte (ändert nichts): ``[{action, name, date_from, date_to, kind, old?}]``.

    ``action``: ``add`` | ``update`` | ``unchanged`` | ``exists`` (von Hand angelegt, gleicher Zeitraum) |
    ``edited`` (importierter Eintrag wurde von Hand geändert) | ``removed`` (von Hand gelöscht)."""
    seen = set((getattr(school, "holiday_import", None) or {}).get("seen") or [])
    by_source = {h.source: h for h in school.holidays if getattr(h, "source", "")}
    manual = [h for h in school.holidays if not getattr(h, "source", "")]
    out = []
    for c in candidates:
        row = {k: c[k] for k in ("name", "date_from", "date_to", "kind")}
        row["source"] = c["source"]
        cur = by_source.get(c["source"])
        if cur is not None:
            if sig_of(cur.name, cur.date_from, cur.date_to, cur.kind) != cur.source_sig:
                row["action"] = "edited"
            elif (cur.name, cur.date_from, cur.date_to, cur.kind) == (c["name"], c["date_from"], c["date_to"], c["kind"]):
                row["action"] = "unchanged"
            else:
                row["action"] = "update"
                row["old"] = {"name": cur.name, "date_from": cur.date_from, "date_to": cur.date_to, "kind": cur.kind}
        elif c["source"] in seen:
            row["action"] = "removed"
        elif any(h.date_from == c["date_from"] and h.date_to == c["date_to"]
                 and (h.kind == c["kind"] or h.name.casefold() == c["name"].casefold()) for h in manual):
            row["action"] = "exists"
        else:
            row["action"] = "add"
        out.append(row)
    return out


def counts(changes: list[dict]) -> dict:
    res = {k: 0 for k in ("add", "update", "unchanged", "exists", "edited", "removed")}
    for c in changes:
        res[c["action"]] += 1
    return res


def apply_plan(school, candidates: list[dict]) -> list[dict]:
    """Führt :func:`plan_changes` am Schuldokument aus (innerhalb von ``store.mutate``)."""
    from schulmanager.models import Holiday

    changes = plan_changes(school, candidates)
    by_source = {h.source: h for h in school.holidays if getattr(h, "source", "")}
    taken = {h.id for h in school.holidays}
    old_seen = list((getattr(school, "holiday_import", None) or {}).get("seen") or [])
    seen = list(old_seen)
    n = len(taken) + 1
    for row in changes:
        act = row["action"]
        if act == "add":
            while f"H{n}" in taken:
                n += 1
            hid = f"H{n}"
            taken.add(hid)
            school.holidays.append(Holiday(hid, row["name"], row["date_from"], row["date_to"], row["kind"],
                                           source=row["source"],
                                           source_sig=sig_of(row["name"], row["date_from"], row["date_to"], row["kind"])))
        elif act == "update":
            h = by_source[row["source"]]
            h.name, h.date_from, h.date_to, h.kind = row["name"], row["date_from"], row["date_to"], row["kind"]
            h.source_sig = sig_of(h.name, h.date_from, h.date_to, h.kind)
        if act in ("add", "update", "unchanged", "edited") and row["source"] not in seen:
            seen.append(row["source"])
    if seen != old_seen:
        school.holiday_import = {**(school.holiday_import or {}), "seen": seen}
    from schulmanager.calendar_utils import apply_auto_year_start
    apply_auto_year_start(school)           # Schuljahresbeginn = Ende der Sommerferien (Einstellung „auto“)
    return changes


# ------------------------------------------------------------------ Ausführen
_status: dict[str, Any] = {"last_run": None, "last_error": None, "last_counts": None, "next_run": None}


def status() -> dict:
    return dict(_status)


def preview(school, years: Optional[list[int]] = None) -> list[dict]:
    cfg = get_settings(school)
    return plan_changes(school, fetch_candidates(cfg, years or current_school_years()))


def run_import(user, years: Optional[list[int]] = None, auto: bool = False) -> dict:
    """Ruft die Quelle ab (außerhalb der Sperre) und übernimmt per ``store.mutate``. Rückgabe ``{changes, counts}``."""
    from .store import get_store

    store = get_store()
    cfg = get_settings(store.school)
    cands = fetch_candidates(cfg, years or current_school_years())
    box: dict[str, list] = {}

    def fn(school):
        box["changes"] = apply_plan(school, cands)

    label = "automatisch " if auto else ""
    where = cfg["country"] + ("/" + cfg["region"] if cfg["region"] else "")
    store.mutate(user, f"Ferien/Feiertage {label}übernommen ({where})", fn, scope=["holidays", "substitutions"])
    changes = box.get("changes", [])
    res = counts(changes)
    _status.update(last_run=datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
                   last_error=None, last_counts=res)
    return {"changes": changes, "counts": res}


# ------------------------------------------------------------------ Automatik
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_wake = threading.Event()
_lock = threading.Lock()


def auto_check() -> float:
    """Ein Automatik-Durchlauf. Rückgabe: Sekunden bis zum nächsten. Wirft nie."""
    try:
        if not config.holiday_import:
            return INTERVAL
        from .store import get_store

        school = get_store().school
        cfg = get_settings(school)
        if not cfg["enabled"] or not cfg["configured"]:
            return INTERVAL
        res = run_import(None, auto=True)
        if res["counts"]["add"] or res["counts"]["update"]:
            log.info("Ferien/Feiertage automatisch übernommen: %s", res["counts"])
        return INTERVAL
    except HolidayImportError as exc:
        _status["last_error"] = str(exc)
        log.warning("Automatischer Ferien-Import: %s", exc)
    except Exception:  # noqa: BLE001 - die Automatik darf den Server nie stören
        _status["last_error"] = "Unerwarteter Fehler beim Ferien-Import"
        log.exception("Automatischer Ferien-Import fehlgeschlagen")
    return RETRY_AFTER_ERROR


def _loop() -> None:
    wait = FIRST_DELAY
    while not _stop.is_set():
        _wake.wait(wait)
        if _stop.is_set():
            break
        _wake.clear()
        wait = auto_check()
        _status["next_run"] = datetime.fromtimestamp(time.time() + wait, timezone.utc).replace(
            microsecond=0, tzinfo=None).isoformat() + "Z"


def start() -> bool:
    global _thread
    if not config.holiday_import:
        log.info("Ferien-Import deaktiviert (SM_HOLIDAY_IMPORT=0)")
        return False
    with _lock:
        if _thread is not None and _thread.is_alive():
            return True
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="sm-holiday-import", daemon=True)
        _thread.start()
    return True


def stop() -> None:
    global _thread
    _stop.set()
    _wake.set()
    with _lock:
        t, _thread = _thread, None
    if t is not None and t.is_alive() and t is not threading.current_thread():
        t.join(2)


def kick() -> None:
    """Automatik sofort anstoßen (z. B. nach dem Einschalten)."""
    _wake.set()
