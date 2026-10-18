# Arbeitsregeln für dieses Repository (Schulmanager)

> **Produktname: Schulpuls** (intern weiter `schulmanager`). Sichtbare Texte nehmen `APP_NAME` aus `frontend/src/brand.ts`
> bzw. `PRODUCT_NAME` aus `schulmanager/branding.py` – nie den Namen hart eintippen. Paket, `SM_*`, Cookies, Docker, Routen,
> Header `X-Schulmanager-*` bleiben. Logo/Varianten: `docs/branding/`.

Gilt für jede Sitzung und jeden Agenten. Ziel: ein Schulmanager, den man vollständig an eine Schule verkaufen kann
(`docs/ANFORDERUNGEN.md`, A-00).

## 1. Erst lesen, dann Code – der Atlas spart Lesezeit
1. Nutze zuerst den **externen Code-Atlas** `C:\Users\reiss\Documents\claude\schulpuls-atlas\` (nicht im Repo):
   `python -X utf8 C:\Users\reiss\Documents\claude\tools\schulpuls-atlas\atlas.py find <begriff>`, dann `INDEX.md` und die
   Bereichsdatei `features/<bereich>.md`. Öffne Quellcode erst danach und nur an den genannten Stellen (Datei:Zeile).
   Die frühere Code-Doku liegt dort unter `doku/code/`.
2. Offene Arbeit: **`docs/OFFENE-PUNKTE.md`** (Stand je Anforderung, bekannte Unstimmigkeiten) und
   **`docs/PRODUKT-BACKLOG.md`** (Arbeitspakete mit Abnahmekriterien). Anforderungen im Wortlaut: `docs/ANFORDERUNGEN.md`.
3. Verträge und Entscheidungen: `docs/ARCHITECTURE.md`; Betrieb: `docs/BETRIEB.md`; Vorschau/Testkonten: `docs/VORSCHAU.md`.
4. Laufende Weiterentwicklung (Runden, Protokoll, Regeln bis 17.10.2026): `docs/AUTOPILOT.md`.

## 2. Nach jeder Code-Änderung
- **Atlas nachziehen**: `atlas.py update` laufen lassen; bei neuen Bereichen/Fallstricken die Bereichsdatei im Atlas
  ergänzen (unterhalb von `<!-- eigene Notizen -->`), `atlas.py check` prüfen. Keine Änderung ohne passenden Atlas-Eintrag.
- **Offene Punkte pflegen**: Status in `docs/OFFENE-PUNKTE.md` anpassen (erledigt/teilweise/fehlt + Nachweis).
- Neue Wünsche des Auftraggebers kommen nach `docs/ANFORDERUNGEN.md` (neue ID), nicht nur in den Chat.

## 3. Qualität
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2; `ruff check .` (Zeilenlänge 120); Tests mit `python -m pytest -q`.
  Rechte **und** Datenumfang (Scopes) immer im Backend prüfen, fremde Daten → 404; jede schreibende Aktion `audit()`;
  personenbezogene Freitexte verschlüsselt (`crypto.encrypt_text`); Codes/Token nur als Hash.
- Datenbank: jede Schemaänderung als Alembic-Revision; Planungsdaten (`models.py`) abwärtskompatibel mit Standardwerten.
- Frontend: React + TypeScript strikt; `cd frontend && npm run lint && npx vitest run`; Feature-Module über
  `src/features/<feature>/module.tsx`; nur vorhandene Icons/Design-Tokens.
- Oberfläche: Deutsch, Personal in Sie-Form, Schüler-Ansichten wie im Bestand. **Keine KI-typischen Erklärtexte** auf den
  Seiten – Hilfe gehört in die Hilfe-Funktion an der Beschriftung (Hover/Rechtsklick/Antippen, A-60). Barrierefrei,
  auf 390 px ohne waagerechtes Scrollen, helles und dunkles Farbschema.
- Datenschutz: keine echten personenbezogenen Daten (auch nicht aus dem Netz) in Code, Tests, Demo oder Doku; Demo- und
  Beispieldaten sind erfunden.
- Prüfen vor Abschluss: eigene Tests, dann komplette Suite und Frontend-Prüfungen; Browser-Rundgang bei UI-Änderungen
  (Chromium unter `/opt/pw-browsers`).

## 4. Zusammenarbeit
- Mehrere Agenten arbeiten oft gleichzeitig: nur Dateien des eigenen Auftrags ändern, geteilte Dateien nur mit kleinen
  Edit-Änderungen nach frischem Lesen; fremde Fehler nicht „reparieren“, sondern melden.
- Keine Commits/Pushes durch Agenten (macht die Hauptsitzung), keine Änderungen an `.github/` ohne Auftrag.
- Keine Prozesse zurücklassen: Server nur auf eigenem Port, am Ende per PID beenden (nie `pkill`/`killall` mit Mustern).
- Keine Hintergrundarbeit ohne Wissen des Auftraggebers; sparsam mit Tokens (komplette Testsuite nicht unnötig oft).

## 5. API-Zugänge und KI-Auffindbarkeit (dauerhafter Standard)
Jede neue Funktion, die Daten für Apps oder KI-Werkzeuge sinnvoll bereitstellt oder ändert, bringt ihre Freigabe gleich mit
(Details: `docs/API-ZUGAENGE.md` §6):
- **Bereich festlegen** (`schulmanager/server/api_scopes.py`, `AREAS`: Label, Beschreibung, Filter, nötige Rechte).
- **Prüfung über die zentrale Funktion**: Route unter `/api/v1/open/…` mit `Depends(open_access("<bereich>"))` (Schreiben:
  `write=True`); bestehende Handler mit dem Konto wiederverwenden, Ergebnis auf `acc.filters` beschneiden, `strip_private`
  anwenden. Nie Gesundheits-, Förder-, Fehlzeiten- oder Nachrichtendaten. Zugänge mit Umfang erreichen keine andere Route.
- **OpenAPI-Beschreibung**: `summary`, `description`, Beispielantwort (erfundene Daten); `/llms.txt`, `/llms-full.txt` und
  `/api/v1/meta/*` entstehen automatisch aus den Routen – keine Schul-/Personendaten dort.
- **Test** (`tests/test_api_access.py`): Bereich verweigert, Filter erzwungen. `test_every_open_route_has_an_area_and_is_documented`
  prüft, dass jede öffentliche Route einem Bereich zugeordnet und beschrieben ist.
- Neue Rechte zusätzlich in `permissions.py`, `docs/ARCHITECTURE.md` §6 (Tabelle, Test!) und `docs/ROLLEN-RECHTE.md`.
