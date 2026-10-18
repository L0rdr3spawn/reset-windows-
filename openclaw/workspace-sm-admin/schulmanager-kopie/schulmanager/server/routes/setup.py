"""Einrichtungs-Assistent einer neuen Schule (``docs/SCHULE-EINRICHTEN.md``, ``docs/PRODUKTREIFE.md``).

* ``GET  /setup/status``             Stand je Schritt (automatisch erkannt oder von Hand vermerkt), Fortschritt, Zähler
* ``PUT  /setup/steps/{key}``        Schritt vermerken: ``done`` | ``skipped`` | ``open`` (Fortschritt bleibt gespeichert)
* ``POST /setup/finish``             Assistent beenden (Hinweisband verschwindet), ``DELETE`` öffnet ihn wieder
* ``GET/PUT /setup/profile``         Schuldaten: Name, Schulform, Bundesland, Adresse, Kontakt, Logo
* ``GET  /school-logo``              Logo der Schule (öffentlich, wie die Anmeldeseite)
* ``POST /setup/holidays``           Ferien und Feiertage für das Bundesland aus dem Profil übernehmen
* ``POST /setup/test-mail``          Testmail an eine Adresse (prüft den SMTP-Versand)

Der Fortschritt liegt in ``system_state`` (``setup``, ``school_profile``) – nicht im Planungsdokument, damit ein
Zurücksetzen/Import der Planung den Assistenten nicht zurückstellt. Die eigentliche Arbeit (Import, Stammdaten,
Zeitraster, Rechte) machen die vorhandenen Seiten; der Assistent verlinkt sie und erkennt den Stand.
"""
from __future__ import annotations

import base64
import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import ops
from ..audit import audit
from ..config import config
from ..db import get_db, iso, utcnow
from ..db_models import User
from ..deps import AuthUser, client_ip, require

router = APIRouter(tags=["Einrichtung"])

SETUP_RIGHTS = ("settings.edit", "users.manage")

#: Schritte in der Reihenfolge des Assistenten: (Schlüssel, optional)
STEPS: tuple[tuple[str, bool], ...] = (
    ("admin", False), ("lizenz", False), ("schule", False), ("schuljahr", False), ("zeitraster", False),
    ("stammdaten", False), ("schueler", False), ("unterricht", False), ("stundenplan", False),
    ("konten", False), ("rechte", False), ("mail", False), ("sso", True),
)
STEP_KEYS = tuple(k for k, _ in STEPS)

SCHOOL_TYPES: dict[str, str] = {
    "grundschule": "Grundschule", "hauptschule": "Hauptschule", "realschule": "Realschule",
    "gymnasium": "Gymnasium", "gesamtschule": "Gesamtschule", "sekundarschule": "Sekundar-/Oberschule",
    "foerderschule": "Förderschule", "berufskolleg": "Berufskolleg / berufsbildende Schule",
    "freie-schule": "Freie Schule (Montessori, Waldorf u. a.)", "sonstige": "Sonstige",
}
STATES: dict[str, str] = {
    "BW": "Baden-Württemberg", "BY": "Bayern", "BE": "Berlin", "BB": "Brandenburg", "HB": "Bremen",
    "HH": "Hamburg", "HE": "Hessen", "MV": "Mecklenburg-Vorpommern", "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen", "RP": "Rheinland-Pfalz", "SL": "Saarland", "SN": "Sachsen",
    "ST": "Sachsen-Anhalt", "SH": "Schleswig-Holstein", "TH": "Thüringen",
}
LOGO_MAX_BYTES = 300_000
_MAGIC = ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


# ---------------------------------------------------------------------------
# Zustand
# ---------------------------------------------------------------------------
def _setup_state() -> dict:
    st = ops.get_state("setup") or {}
    marked = {k: v for k, v in (st.get("marked") or {}).items() if k in STEP_KEYS and v in ("done", "skipped")}
    return {"marked": marked, "finished_at": st.get("finished_at")}


def _profile() -> dict:
    p = ops.get_state("school_profile") or {}
    return {"school_type": p.get("school_type") or "", "state": p.get("state") or "", "street": p.get("street") or "",
            "zip": p.get("zip") or "", "city": p.get("city") or "", "phone": p.get("phone") or "",
            "email": p.get("email") or "", "website": p.get("website") or "",
            "logo_mime": p.get("logo_mime") or "", "logo": p.get("logo") or ""}


def _public_profile() -> dict:
    p = _profile()
    p["has_logo"] = bool(p.pop("logo"))
    p.pop("logo_mime")
    return p


@router.get("/setup/status")
def setup_status(user: AuthUser = Depends(require(*SETUP_RIGHTS, any_of=True)),
                 db: Session = Depends(get_db)) -> dict:
    from .. import licensing
    from ..store import get_store

    school = get_store().school
    st = school.settings
    counts = {name: len(getattr(school, name)) for name in
              ("sites", "subjects", "teachers", "rooms", "classes", "students", "courses", "curricula", "lessons",
               "holidays")}
    roles = dict(db.execute(select(User.role, func.count(User.id)).where(User.active.is_(True)).group_by(User.role))
                 .all())
    lic = licensing.status()
    profile = _public_profile()
    state = _setup_state()
    me = db.get(User, user.id)
    sso_on = False
    try:
        from .. import sso_providers as sp

        sso_on = any(sp.resolve(db, pid).enabled for pid in sp.PROVIDERS)
    except Exception:  # noqa: BLE001 - SSO ist optional; Fehler darf den Assistenten nicht stören
        sso_on = False
    auto = {
        "admin": bool(me and me.totp_enabled) or "admin" in config.require_2fa_roles,
        "lizenz": lic.get("state") in ("valid", "grace") or not lic.get("enforced"),
        "schule": bool(st.school_name and st.school_name != "Meine Schule") and counts["sites"] > 0
        and bool(profile["school_type"]) and bool(profile["state"]),
        "schuljahr": bool(st.school_year_start) and counts["holidays"] > 0,
        "zeitraster": False,
        "stammdaten": all(counts[k] > 0 for k in ("subjects", "teachers", "rooms", "classes")),
        "schueler": counts["students"] > 0,
        "unterricht": counts["courses"] > 0 or counts["curricula"] > 0,
        "stundenplan": counts["lessons"] > 0,
        "konten": sum(v for k, v in roles.items() if k in ("lehrer", "schueler", "eltern")) > 0,
        "rechte": False,
        "mail": config.smtp_enabled and not config.dev_outbox,
        "sso": sso_on,
    }
    steps = []
    for key, optional in STEPS:
        mark = state["marked"].get(key)
        done = auto[key] or mark == "done"
        steps.append({"key": key, "done": done, "skipped": mark == "skipped" and not done, "optional": optional,
                      "auto": auto[key], "marked": mark})
    open_required = [s for s in steps if not s["done"] and not s["skipped"] and not s["optional"]]
    current = next((s["key"] for s in steps if not s["done"] and not s["skipped"]), None)
    empty = counts["classes"] == 0 and counts["teachers"] == 0
    finished = bool(state["finished_at"])
    return {"school_name": st.school_name, "license": {k: lic.get(k) for k in ("state", "enforced", "message")},
            "counts": counts, "accounts": roles, "steps": steps, "current": current,
            "profile": profile, "finished": finished, "finished_at": state["finished_at"],
            "ready_to_finish": not open_required, "empty": empty,
            "banner": (not finished) and config.mode != "demo" and (empty or config.is_production_mode),
            "mode": config.mode,
            "mail": {"smtp": config.smtp_enabled, "dev_outbox": config.dev_outbox},
            "bundesland": STATES.get(profile["state"], "")}


class StepIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["done", "skipped", "open"]


@router.put("/setup/steps/{key}")
def mark_step(key: str, body: StepIn, request: Request, user: AuthUser = Depends(require(*SETUP_RIGHTS, any_of=True)),
              db: Session = Depends(get_db)) -> dict:
    """Schritt vermerken (erledigt/übersprungen/offen). Der Stand bleibt gespeichert, man kann später weitermachen."""
    if key not in STEP_KEYS:
        raise HTTPException(404, "Unbekannter Schritt")
    state = _setup_state()
    if body.state == "open":
        state["marked"].pop(key, None)
    else:
        state["marked"][key] = body.state
    ops.set_state("setup", state, user.username)
    audit(db, user, "setup.step", key, {"state": body.state}, ip=client_ip(request))
    db.commit()
    return {"key": key, "state": body.state}


@router.post("/setup/finish")
def finish(request: Request, user: AuthUser = Depends(require(*SETUP_RIGHTS, any_of=True)),
           db: Session = Depends(get_db)) -> dict:
    state = _setup_state()
    state["finished_at"] = iso(utcnow())
    ops.set_state("setup", state, user.username)
    audit(db, user, "setup.finish", "setup", ip=client_ip(request))
    db.commit()
    return {"finished_at": state["finished_at"]}


@router.delete("/setup/finish")
def reopen(request: Request, user: AuthUser = Depends(require(*SETUP_RIGHTS, any_of=True)),
           db: Session = Depends(get_db)) -> dict:
    state = _setup_state()
    state["finished_at"] = None
    ops.set_state("setup", state, user.username)
    audit(db, user, "setup.reopen", "setup", ip=client_ip(request))
    db.commit()
    return {"finished_at": None}


# ---------------------------------------------------------------------------
# Schuldaten
# ---------------------------------------------------------------------------
class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    school_name: Optional[str] = Field(None, min_length=1, max_length=200)
    school_type: Optional[str] = Field(None, max_length=30)
    state: Optional[str] = Field(None, max_length=2)
    street: Optional[str] = Field(None, max_length=200)
    zip: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=40)
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=200)
    #: neues Logo als data-URL (PNG/JPEG, höchstens 300 kB); ``""`` entfernt das Logo
    logo: Optional[str] = Field(None, max_length=450_000)


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ZIP = re.compile(r"^[0-9A-Za-z -]{0,10}$")


def _decode_logo(data_url: str) -> tuple[str, str]:
    m = re.match(r"^data:(image/(?:png|jpeg));base64,([A-Za-z0-9+/=\s]+)$", data_url)
    if not m:
        raise HTTPException(422, "Logo: nur PNG oder JPEG")
    try:
        raw = base64.b64decode(m.group(2), validate=False)
    except ValueError:
        raise HTTPException(422, "Logo: ungültige Datei") from None
    if len(raw) > LOGO_MAX_BYTES:
        raise HTTPException(422, "Logo: höchstens 300 kB")
    mime = next((mt for magic, mt in _MAGIC if raw.startswith(magic)), None)
    if mime is None or mime != m.group(1):
        raise HTTPException(422, "Logo: Dateiinhalt passt nicht zu PNG/JPEG")
    return mime, base64.b64encode(raw).decode("ascii")


@router.get("/setup/profile")
def get_profile(_user: AuthUser = Depends(require("settings.edit"))) -> dict:
    from ..store import get_store

    return {"school_name": get_store().school.settings.school_name, **_public_profile(),
            "school_types": SCHOOL_TYPES, "states": STATES}


@router.put("/setup/profile")
def put_profile(body: ProfileIn, request: Request, user: AuthUser = Depends(require("settings.edit")),
                db: Session = Depends(get_db)) -> dict:
    from .features_common import mutate

    data = body.model_dump(exclude_unset=True)
    if data.get("school_type") and data["school_type"] not in SCHOOL_TYPES:
        raise HTTPException(422, "Unbekannte Schulform")
    if data.get("state") and data["state"] not in STATES:
        raise HTTPException(422, "Unbekanntes Bundesland")
    if data.get("email") and not _EMAIL.match(data["email"]):
        raise HTTPException(422, "Ungültige E-Mail-Adresse")
    if data.get("zip") is not None and not _ZIP.match(data["zip"]):
        raise HTTPException(422, "Ungültige Postleitzahl")
    if data.get("website") and not re.match(r"^https?://[^\s]+$", data["website"]):
        raise HTTPException(422, "Webadresse muss mit http:// oder https:// beginnen")
    profile = ops.get_state("school_profile") or {}
    if "logo" in data:
        if data["logo"]:
            profile["logo_mime"], profile["logo"] = _decode_logo(data["logo"])
        else:
            profile.pop("logo", None)
            profile.pop("logo_mime", None)
    for key in ("school_type", "state", "street", "zip", "city", "phone", "email", "website"):
        if key in data:
            profile[key] = (data[key] or "").strip()
    name = (data.get("school_name") or "").strip()
    if "school_name" in data and not name:
        raise HTTPException(422, "Der Name der Schule darf nicht leer sein")
    ops.set_state("school_profile", profile, user.username)
    if name:
        def fn(school):
            school.settings.school_name = name

        mutate(user, "Schulname geändert", fn, scope=["settings"])
    audit(db, user, "setup.profile", "school", {"fields": sorted(k for k in data if k != "logo"),
                                                "logo": "logo" in data}, ip=client_ip(request))
    db.commit()
    return get_profile(user)


@router.get("/school-logo")
def school_logo() -> Response:
    """Logo der Schule (ohne Anmeldung, wie Name und Anmeldeseite)."""
    p = _profile()
    if not p["logo"]:
        raise HTTPException(404, "Kein Logo hinterlegt")
    return Response(base64.b64decode(p["logo"]), media_type=p["logo_mime"] or "image/png",
                    headers={"Cache-Control": "public, max-age=300", "X-Content-Type-Options": "nosniff"})


# ---------------------------------------------------------------------------
# Ferien, Testmail
# ---------------------------------------------------------------------------
@router.post("/setup/holidays")
def import_holidays(request: Request, user: AuthUser = Depends(require("settings.edit", "masterdata.edit")),
                    db: Session = Depends(get_db)) -> dict:
    """Ferien und Feiertage für das Bundesland aus den Schuldaten übernehmen (laufendes und nächstes Schuljahr)."""
    from .. import holiday_import as hi
    from .features_common import mutate

    state = _profile()["state"]
    if state not in STATES:
        raise HTTPException(409, "Bitte zuerst das Bundesland in den Schuldaten wählen")
    cfg = {"enabled": True, "country": "DE", "region": f"DE-{state}", "language": "de"}
    try:
        cfg = hi.clean_settings(cfg)

        def fn(school):
            school.holiday_import = {**(school.holiday_import or {}), **cfg}

        mutate(user, "Einstellungen für den Ferien-Import geändert", fn, scope=["settings"])
        result = hi.run_import(user, None)
    except hi.HolidayImportError as exc:
        raise HTTPException(exc.status, str(exc)) from None
    audit(db, user, "setup.holidays", f"DE-{state}", ip=client_ip(request))
    db.commit()
    return result


class TestMailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to: str = Field(min_length=3, max_length=200)


@router.post("/setup/test-mail")
def test_mail(body: TestMailIn, request: Request, user: AuthUser = Depends(require("settings.edit")),
              db: Session = Depends(get_db)) -> dict:
    """Schickt eine Testmail über den eingerichteten SMTP-Server (Fehler kommen als Klartext zurück)."""
    from .. import notify

    if not _EMAIL.match(body.to.strip()):
        raise HTTPException(422, "Ungültige E-Mail-Adresse")
    if not config.smtp_enabled:
        raise HTTPException(409, "E-Mail-Versand ist nicht eingerichtet (SM_SMTP_HOST und SM_SMTP_FROM)")
    ok, error = True, ""
    try:
        notify.send_email(body.to.strip(), f"Testnachricht von {config.app_name}",
                          f"Diese Nachricht bestätigt, dass der E-Mail-Versand von {config.app_name} funktioniert.")
    except Exception as exc:  # noqa: BLE001 - SMTP-Fehler als Klartext für die Administration
        ok, error = False, f"{type(exc).__name__}: {exc}"[:300]
    audit(db, user, "setup.test_mail", "mail", {"ok": ok}, ip=client_ip(request))
    db.commit()
    return {"ok": ok, "error": error}
