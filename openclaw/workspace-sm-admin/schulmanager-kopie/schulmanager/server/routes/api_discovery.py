"""Auffindbarkeit für KIs und Apps: ``/llms.txt``, ``/llms-full.txt``, ``/robots.txt``, ``/.well-known/…`` und die
Struktur-Metadaten der öffentlichen API (``/api/v1/meta/scopes``, ``/api/v1/meta/openapi.json``).

Alles hier ist ohne Anmeldung erreichbar und enthält **nur Struktur** (Begriffe, Endpunkte, Bereiche) – nie Schul- oder
Personendaten. Die Endpunktlisten werden aus den tatsächlich registrierten Routen unter ``/api/v1/open`` erzeugt
(``api_scopes.open_routes``): neue Routen erscheinen automatisch.
"""
from __future__ import annotations

import copy
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from schulmanager.branding import PRODUCT_NAME
from schulmanager.server import api_scopes as scopes
from schulmanager.server.config import APP_VERSION, config

router = APIRouter(tags=["Öffentliche API"])
public_router = APIRouter(include_in_schema=False)

API_VERSION = "v1"
TEXT = "text/plain; charset=utf-8"
_CACHE = {"Cache-Control": "public, max-age=3600"}


def _base(request: Request) -> str:
    """Basisadresse: konfigurierte ``SM_BASE_URL`` (nie der Host-Header der Anfrage)."""
    return config.base_url or str(request.base_url).rstrip("/")


# ----------------------------------------------------------------------------------- Metadaten
def scopes_document(request: Request) -> dict[str, Any]:
    base = _base(request)
    return {
        "api": f"{PRODUCT_NAME} – öffentliche API", "version": API_VERSION, "app_version": APP_VERSION,
        "base_url": f"{base}/api/v1/open",
        "auth": {"scheme": "bearer", "header": "Authorization: Bearer <token>",
                 "how": "API-Zugang in der Oberfläche unter „API-Zugänge“ anlegen; das Token wird nur einmal angezeigt."},
        "limits": {"default_requests_per_minute": scopes.DEFAULT_RATE, "max_requests_per_minute": scopes.MAX_RATE,
                   "max_valid_days": scopes.MAX_EXPIRES_DAYS, "response_on_limit": 429},
        "areas": [{"id": a, "label": m["label"], "description": m["description"], "filters": m["filters"],
                   "write": bool(m.get("write"))} for a, m in scopes.AREAS.items()],
        "filters": [{"id": k, "label": v} for k, v in scopes.FILTER_LABELS.items()],
        "filter_semantics": "classes/teachers/rooms/students ergeben zusammen die erlaubte Menge (ODER); sites schränkt "
                            "zusätzlich ein (UND). Kein Filter = alles, was das Konto des Zugangs sieht.",
        "not_offered": [{"id": k, "reason": v} for k, v in scopes.NOT_OFFERED.items()],
        "endpoints": [{"method": r["method"], "path": r["path"], "area": r["area"], "write": r["write"],
                       "summary": r["summary"]} for r in scopes.open_routes(request.app) if r["area"] != "meta"],
        "discovery": {"llms_txt": f"{base}/llms.txt", "llms_full_txt": f"{base}/llms-full.txt",
                      "openapi": f"{base}/api/v1/meta/openapi.json"},
    }


@router.get("/meta/scopes", summary="Bereiche, Filter und Endpunkte der öffentlichen API (ohne Anmeldung)",
            description="Maschinenlesbare Übersicht: welche Bereiche es gibt, welche Filter, welche Endpunkte zu "
                        "welchem Bereich gehören und welche Grenzen gelten. Enthält keine Schul- oder Personendaten.",
            dependencies=[Depends(scopes.public_meta)])
def meta_scopes(request: Request) -> JSONResponse:
    return JSONResponse(scopes_document(request), headers=_CACHE)


def _collect_refs(obj: Any, found: set[str]) -> None:
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            found.add(ref.rsplit("/", 1)[1])
        for v in obj.values():
            _collect_refs(v, found)
    elif isinstance(obj, list):
        for v in obj:
            _collect_refs(v, found)


def public_openapi(request: Request) -> dict[str, Any]:
    """OpenAPI-Dokument nur der öffentlichen API (``/api/v1/open`` und ``/api/v1/meta``) – unabhängig davon, ob die
    vollständige Dokumentation (``SM_ENABLE_DOCS``) eingeschaltet ist."""
    full = copy.deepcopy(request.app.openapi())
    paths = {p: v for p, v in full.get("paths", {}).items() if p.startswith(("/api/v1/open", "/api/v1/meta"))}
    for p, ops in paths.items():
        if p.startswith("/api/v1/open"):
            for op in ops.values():
                if isinstance(op, dict):
                    op["security"] = [{"bearerAuth": []}]
    needed: set[str] = set()
    _collect_refs(paths, needed)
    comps = full.get("components", {}).get("schemas", {})
    queue = list(needed)
    while queue:
        name = queue.pop()
        sub: set[str] = set()
        _collect_refs(comps.get(name, {}), sub)
        for n in sub - needed:
            needed.add(n)
            queue.append(n)
    base = _base(request)
    return {
        "openapi": full.get("openapi", "3.1.0"),
        "info": {"title": f"{PRODUCT_NAME} – öffentliche API", "version": API_VERSION,
                 "description": "Lesender (und optional schreibender) Zugriff auf Stundenplan, Vertretung, Termine, Räume "
                                "und Mitteilungen im Umfang eines API-Zugangs. Beschreibung für KIs: /llms.txt"},
        "servers": [{"url": base}],
        "paths": paths,
        "components": {"schemas": {n: comps[n] for n in sorted(needed) if n in comps},
                       "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer",
                                                          "description": "API-Zugang (Token beginnt mit sma_)"}}},
    }


@router.get("/meta/openapi.json", summary="OpenAPI-Beschreibung der öffentlichen API (ohne Anmeldung)",
            description="Nur die Routen unter /api/v1/open – ohne interne Verwaltungs-Endpunkte.",
            dependencies=[Depends(scopes.public_meta)])
def meta_openapi(request: Request) -> JSONResponse:
    return JSONResponse(public_openapi(request), headers=_CACHE)


# ------------------------------------------------------------------------------------- llms.txt
GLOSSARY = [
    ("Klasse", "Schülergruppe mit Kürzel (z. B. `5a`), Stufe (`grade`) und Standort."),
    ("Kurs", "Unterrichtsangebot (Fach + Lehrkraft + Klassen), kann in Kursteile gegliedert sein (z. B. Religion nach "
             "Konfession)."),
    ("Stundenplan", "Wochenraster aus Stunden (Tag + Stundennummer, 0-basiert) für eine Klasse, Lehrkraft, einen Raum "
                    "oder Schüler. Die Zeiten der Stunden stehen in der Antwort."),
    ("Vertretung / Entfall / Raumänderung", "Abweichungen vom Stundenplan an einem Datum (`kind`: `vertretung`, "
                                            "`entfall`, `raumaenderung`, `klausur` …)."),
    ("Kürzel", "Kurze Kennung von Lehrkräften (z. B. `MUS`), Räumen und Klassen – dient in allen Aufrufen als ID."),
    ("Standort", "Schulgebäude bzw. Außenstelle; `site` an Klassen, Räumen, Mitteilungen."),
    ("Mitteilung", "Eintrag am schwarzen Brett (für alle oder bestimmte Klassen, mit Gültigkeitszeitraum)."),
    ("Bereich", "Themenblock eines API-Zugangs (z. B. `timetable`, `substitutions`). Ein Zugang umfasst nur gewählte Bereiche."),
    ("Filter", "Beschränkung eines Zugangs auf bestimmte Klassen, Lehrkräfte, Räume, Schüler/innen oder Standorte."),
]


def _endpoint_lines(request: Request, base: str, *, full: bool) -> list[str]:
    lines = []
    for r in scopes.open_routes(request.app):
        if r["area"] == "meta":
            continue
        desc = r["description"].split("\n\n")[0].replace("\n", " ") if full and r["description"] else ""
        label = "" if r["method"] == "GET" else f" ({'schreibend' if r['write'] else r['method']})"
        lines.append(f"- [{r['method']} {r['path']}]({base}{r['path']}): [{r['area']}] {r['summary']}{label}"
                     + (f" – {desc}" if desc and desc != r["summary"] else ""))
    return lines


def llms_txt(request: Request, *, full: bool = False) -> str:
    base = _base(request)
    out = [
        f"# {PRODUCT_NAME}",
        "",
        "> Schulverwaltung mit Stundenplan, Vertretungsplan, Terminen, Räumen und Mitteilungen. "
        "School management software (timetable, substitutions, calendar, rooms, announcements) with a read-oriented "
        "REST API for apps and AI tools. Zugriff nur mit einem von der Schule ausgegebenen API-Zugang (Bearer-Token) – "
        "diese Datei enthält keine Schul- oder Personendaten.",
        "",
        "Die öffentliche API liegt unter `/api/v1/open/…` (versioniert, JSON, UTF-8, Datum `JJJJ-MM-TT`). "
        "Ein API-Zugang gilt nur für ausgewählte **Bereiche** und optional nur für bestimmte Klassen, Lehrkräfte, Räume, "
        "Schüler/innen oder Standorte. Er kann nie mehr sehen als das Konto, das ihn ausgegeben hat.",
        "",
        "## Anmeldung",
        "",
        f"- Header `Authorization: Bearer <token>`; das Token (beginnt mit `sma_`) gibt Personal unter „API-Zugänge“ "
        f"aus, es wird nur einmal angezeigt. Ohne Token: `401`; Bereich/Filter nicht im Umfang: `403`; "
        f"zu viele Anfragen (Standard {scopes.DEFAULT_RATE}/Minute): `429` mit `Retry-After`.",
        f"- Beispiel: `curl -H \"Authorization: Bearer $TOKEN\" {base}/api/v1/open/substitutions`",
        "",
        "## Beschreibungen",
        "",
        f"- [OpenAPI der öffentlichen API]({base}/api/v1/meta/openapi.json): maschinenlesbar, nur `/open`",
        f"- [Bereiche, Filter, Grenzen]({base}/api/v1/meta/scopes): JSON-Übersicht",
        f"- [Ausführliche Fassung dieser Datei]({base}/llms-full.txt)",
        "",
        "## Endpunkte (`[bereich]` = nötiger Bereich des Zugangs)",
        "",
        *_endpoint_lines(request, base, full=False),
        "",
        "## Bereiche",
        "",
        *[f"- `{a}` – {m['label']}: {m['description']}" for a, m in scopes.AREAS.items()],
        "",
        "## Optional",
        "",
        "- Es gibt bewusst keine Bereiche für private Nachrichten, Chats, Krankmeldungen, Atteste, Förder- und "
        "Fehlzeitendaten, Noten oder Konten.",
    ]
    if not full:
        return "\n".join(out) + "\n"
    out += ["", "# Ausführliche Beschreibung", "", "## Begriffe", ""]
    out += [f"- **{t}**: {d}" for t, d in GLOSSARY]
    out += ["", "## Filter", "",
            "- Filterarten: " + ", ".join(f"`{k}` ({v})" for k, v in scopes.FILTER_LABELS.items()) + ".",
            "- `classes`, `teachers`, `rooms`, `students` ergeben zusammen die erlaubte Menge (ODER): Ein Zugang für "
            "Klasse `5a` und Lehrkraft `MUS` sieht Pläne beider. `sites` schränkt zusätzlich ein (UND).",
            "- Pläne außerhalb der Filter antworten mit `403` („Nicht im Umfang dieses Zugangs“). Ohne Filter gilt der "
            "volle Umfang des ausgebenden Kontos (Lehrkräfte z. B. nur Klassen, die sie leiten).",
            "", "## Antworten und Fehler", "",
            "- Erfolg: `200` (Anlegen: `201`) mit JSON. Fehler: `{\"detail\": \"Text\"}` mit `401` (Token fehlt/ungültig/"
            "abgelaufen/widerrufen), `403` (nicht im Umfang, IP nicht freigegeben), `404`, `422` (ungültige Parameter), "
            "`429` (Ratenlimit).",
            "- Zeiten: Datum `JJJJ-MM-TT`; Stunden sind 0-basiert (`start: 0` = erste Stunde); Wochentage `0` = Montag.",
            "- Vertretungen enthalten nie Abwesenheitsgründe, Aufsichten oder interne Warnungen.",
            "", "## Endpunkte im Detail", "", *_endpoint_lines(request, base, full=True),
            "", "## Datenschutz und Grenzen", "",
            "- Zugänge sind befristet (höchstens 365 Tage), können jederzeit widerrufen werden und werden protokolliert "
            "(letzte Nutzung, Aufrufe).",
            "- Gesundheits-, Förder- und Fehlzeitendaten sowie private Nachrichten sind nie über einen Zugang abrufbar.",
            "- Schülerpläne sind personenbezogen: nur an Anwendungen weitergeben, für die die Schule zugestimmt hat.",
            "- Crawler: `/robots.txt` sperrt die Oberfläche und die API; erlaubt sind nur die Beschreibungsdateien.",
            "", "## Hinweise für KI-Assistenten", "",
            "- Erst `/api/v1/open/classes`, `/teachers`, `/rooms` abfragen, um gültige Kürzel zu erhalten, dann den "
            "Plan abrufen.",
            "- Keine Zugangsdaten raten oder weitergeben; bei `403` den Nutzer bitten, den Zugang um den Bereich oder "
            "Filter zu erweitern (neuer Zugang), statt andere Wege zu suchen.",
            "- Antworten sind Momentaufnahmen; für Vertretungen immer das gewünschte Datum angeben."]
    return "\n".join(out) + "\n"


@public_router.get("/llms.txt")
def llms(request: Request) -> PlainTextResponse:
    return PlainTextResponse(llms_txt(request), media_type=TEXT, headers=_CACHE)


@public_router.get("/llms-full.txt")
def llms_full(request: Request) -> PlainTextResponse:
    return PlainTextResponse(llms_txt(request, full=True), media_type=TEXT, headers=_CACHE)


@public_router.get("/.well-known/llms.txt")
def well_known_llms(request: Request) -> PlainTextResponse:
    return PlainTextResponse(llms_txt(request), media_type=TEXT, headers=_CACHE)


@public_router.get("/.well-known/api-catalog")
def api_catalog(request: Request) -> JSONResponse:
    """API-Katalog nach RFC 9727 (``application/linkset+json``)."""
    base = _base(request)
    body = {"linkset": [{
        "anchor": f"{base}/api/v1/open",
        "service-desc": [{"href": f"{base}/api/v1/meta/openapi.json", "type": "application/vnd.oai.openapi+json"}],
        "service-doc": [{"href": f"{base}/llms.txt", "type": "text/plain"},
                        {"href": f"{base}/llms-full.txt", "type": "text/plain"}],
        "service-meta": [{"href": f"{base}/api/v1/meta/scopes", "type": "application/json"}],
    }]}
    return JSONResponse(body, media_type="application/linkset+json", headers=_CACHE)


@public_router.get("/robots.txt")
def robots() -> PlainTextResponse:
    """Nichts Persönliches indexieren: alles gesperrt, nur die Beschreibungsdateien für KIs sind erlaubt."""
    text = ("User-agent: *\n"
            "Allow: /llms.txt\nAllow: /llms-full.txt\nAllow: /.well-known/api-catalog\nAllow: /.well-known/llms.txt\n"
            "Allow: /api/v1/meta/\n"
            "Disallow: /\n")
    return PlainTextResponse(text, media_type=TEXT, headers=_CACHE)
