# API-Zugänge und KI-Auffindbarkeit

Stand 12.10.2026. Wunsch des Auftraggebers: Administration (und Lehrkräfte für ihren Bereich) geben Zugänge für Apps oder
KI-Werkzeuge aus – nur für ausgewählte Daten; die Anwendung ist für KIs auffindbar und verständlich; beides gilt für jede
künftige Funktion (siehe Abschnitt 6 und `CLAUDE.md`).

## 1. Was es gibt

| Baustein | Ort |
|---|---|
| Zugang (Token) mit Umfang | `db_models.ApiToken` (neue Spalten `purpose`, `scope`, `ip_allow`, `rate_limit`, `revoked_at`, `use_count`), Migration `0027_api_access` |
| Nutzungsprotokoll | `feature_models/api_access.py` (`api_token_log`, letzte 200 Aufrufe je Zugang) + Audit `api_access.create/revoke/announcement` |
| Bereiche, Filter, Durchsetzung | `server/api_scopes.py` |
| Öffentliche, versionierte API | `server/routes/api_open.py` → `/api/v1/open/…` |
| Verwaltung (Anlegen, Liste, Log, Widerruf) | `server/routes/features_api_access.py` → `/api/v1/api-access…` |
| Auffindbarkeit | `server/routes/api_discovery.py` → `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/.well-known/api-catalog`, `/.well-known/llms.txt`, `/api/v1/meta/scopes`, `/api/v1/meta/openapi.json` |
| Oberfläche | `frontend/src/features/api-zugaenge/` (Seite „API-Zugänge“) |
| Rechte | `api.own` (Personal: eigene Zugänge), `api.manage` (Administration, Schulleitung: alle sehen, prüfen, widerrufen) |
| Tests | `tests/test_api_access.py` |

Bereits vorher vorhanden und unverändert: persönliche API-Tokens (`smt_…`, `POST /users/{id}/api-token`, gelten wie das Konto),
iCal-Feeds (`/ical/{token}.ics`), OpenAPI/Swagger (`SM_ENABLE_DOCS=0|admin|1`, `/api/docs`; Standard: nur Administratoren, lokal ausgeliefert).

## 2. Ein Zugang

* Name/Zweck, Ersteller (= Konto, dem der Zugang gehört), Ablauf (1–365 Tage, Standard 90; kein unbefristeter Zugang),
  **Bereiche**, **Filter**, optional **Schreibrechte**, optional **IP-Beschränkung** (Adressen oder Netze, z. B. `192.168.0.0/24`),
  **Ratenlimit** (Anfragen/Minute, Standard 60, höchstens 600; je Serverprozess).
* Das Token (`sma_…`) steht **nur** in der Antwort des Anlegens; gespeichert wird der HMAC-Hash. Anlegen nur nach Anmeldung in
  der Oberfläche (ein Token stellt keine Zugänge aus), höchstens 25 aktive je Konto.
* Widerruf (`DELETE /api-access/{id}`) wirkt sofort; abgelaufene Zugänge bleiben 30 Tage sichtbar (Protokoll), dann räumt die
  Wartung auf. Wird das Konto gesperrt/gelöscht, ist der Zugang tot.
* **Der Zugang handelt als sein Konto**: Rechte und Datenumfang des Kontos werden bei jeder Anfrage neu ausgewertet. Er kann
  also nie mehr als das Konto – und zusätzlich nur das Freigegebene.

### Bereiche (`api_scopes.AREAS`)

| Bereich | Routen unter `/api/v1/open` | Filter | Recht des Kontos (eines davon) |
|---|---|---|---|
| `timetable` | `timetable/{class\|teacher\|student\|room}/{ref}` (Raum zusätzlich Bereich `rooms`) | Klassen, Lehrkräfte, Schüler, Räume, Standorte | `plans.read_all`, `timetable.edit` |
| `substitutions` | `substitutions`, `substitutions/range` | Klassen, Lehrkräfte, Räume, Standorte | `substitution.read` |
| `calendar` | `calendar/school-year`, `calendar/week` | Klassen, Lehrkräfte, Schüler, Räume, Standorte | `plans.read_all`, `timetable.edit` |
| `rooms` | `rooms` | Räume, Standorte | `rooms.read`, `timetable.edit` |
| `announcements` | `announcements` (lesen), `POST announcements` (Schreibrecht) | Klassen, Standorte | – (lesen); `announcement.post` (schreiben) |
| `directory` | `classes`, `teachers` (nur Kürzel+Name), `sites` | Klassen, Standorte | `plans.read_all`, `masterdata.read`, `timetable.edit` |

Bewusst **nicht** angeboten (`api_scopes.NOT_OFFERED`): private Nachrichten/Chats, Krankmeldungen, Atteste, Nachteilsausgleich/
Förderdaten, Fehlzeiten, Noten, Schülerlisten, Konten. Zusätzlich entfernt `strip_private` aus wiederverwendeten Antworten
Schlüssel mit Gesundheits-/Förder-/Fehlzeitenbezug (`reason`, `attendance`, `support`, `homework`, Nachschreibtermine …).

### Filter

`classes`, `teachers`, `rooms`, `students` ergeben zusammen die **erlaubte Menge** (ODER: Klasse 5a *oder* Lehrkraft MUS);
`sites` schränkt zusätzlich ein (UND). Ohne Filter gilt alles, was das Konto sieht. Pläne außerhalb → `403`.
Beim Anlegen prüft `normalize_scope`, dass das Konto nur freigibt, was es selbst sieht: Klassen laut `plan_class_ids`
(Lehrkräfte: geleitete Klassen), fremde Lehrkräfte/Räume nur mit uneingeschränktem Planzugriff, Schüler nur sichtbare.

## 3. Zentrale Durchsetzung

1. `deps.authenticate`: Zugang mit `scope` → `api_scopes.check_request` lehnt **jede Route außerhalb `/api/v1/open/…`** ab (`403`),
   prüft die IP-Beschränkung und das Ratenlimit (`429` + `Retry-After`); widerrufen/abgelaufen → `401 invalid_token`.
2. Jede Route der öffentlichen API hängt an `Depends(open_access("<bereich>"))` (Schreiben: `write=True`): Bereich muss im
   Zugang stehen, sonst `403`; die Nutzung wird protokolliert.
3. Der Handler benutzt die bestehenden Funktionen mit dem Konto (`AuthUser`) und beschneidet das Ergebnis auf die Filter.

## 4. Auffindbarkeit für KIs

* `/llms.txt` (kurz) und `/llms-full.txt` (Begriffe, Filter, Fehler, Hinweise) nach dem llms.txt-Vorschlag; die Endpunktlisten
  werden aus den tatsächlich registrierten Routen erzeugt – neue Routen erscheinen automatisch. Nur Struktur, nie Schul- oder
  Personendaten (Test prüft das gegen die Demo-Schule). Basisadresse = `SM_BASE_URL`.
* `/.well-known/api-catalog` (RFC 9727, Linkset mit OpenAPI und Beschreibungen), `/.well-known/llms.txt`.
* `/api/v1/meta/openapi.json`: OpenAPI nur der öffentlichen API (unabhängig von `SM_ENABLE_DOCS`, ohne Anmeldung lesbar); `/api/v1/meta/scopes`:
  Bereiche, Filter, Grenzen, Endpunkte als JSON.
* `/robots.txt`: alles gesperrt, erlaubt nur die Beschreibungsdateien (`/llms*.txt`, `/.well-known/…`, `/api/v1/meta/`).

## 5. Anlegen eines Zugangs

Oberfläche: **API-Zugänge** (Menü Verwaltung) → „Neuer Zugang“ → Name/Zweck → Bereiche → Filter → Laufzeit/IP/Limit →
Vorschau „Dieser Zugang darf: …“ → Anlegen → Token kopieren (wird nicht noch einmal gezeigt). Dazu ein `curl`-Beispiel.

API: `POST /api/v1/api-access` (Sitzung + CSRF) mit

```json
{"name": "Aushang-Monitor", "purpose": "Vertretungsplan im Foyer", "expires_days": 90,
 "areas": ["substitutions", "timetable"], "write": [],
 "filters": {"classes": ["5a", "5b"], "sites": []}, "ip_allow": ["192.168.0.0/24"], "rate_limit": 60}
```

`POST /api-access/preview` liefert dieselbe Prüfung ohne Anlegen. `GET /api-access/meta` nennt die Bereiche und Filterwerte, die das
Konto freigeben darf.

## 6. Standard für neue Funktionen (verbindlich)

Jede neue Funktion, die Daten liefern oder ändern kann, die für Apps/KIs sinnvoll sind, bringt gleich mit:

1. **Bereich festlegen**: bestehenden Bereich in `api_scopes.AREAS` nutzen oder neu eintragen (Label, Beschreibung, Filter, nötige Rechte).
2. **Route** unter `/api/v1/open/…` in `routes/api_open.py` (oder eigenem Modul mit `APIRouter(prefix="/open")`) mit
   `Depends(open_access("<bereich>"))`; vorhandene Handler mit dem Konto wiederverwenden, Ergebnis auf `acc.filters` beschneiden,
   `strip_private` anwenden, nie Gesundheits-/Förder-/Fehlzeitendaten.
3. **OpenAPI-Beschreibung**: `summary`, `description`, Beispielantwort (erfundene Daten) – `/llms.txt` und `/api/v1/meta/*` ziehen es
   automatisch.
4. **Rechte-Dokumentation**: nötige Rechte im Bereich eintragen; neue Rechte in `permissions.py`, `ARCHITECTURE.md` §6, `ROLLEN-RECHTE.md`.
5. **Test** in `tests/test_api_access.py` (Bereich verweigert, Filter erzwungen). `test_every_open_route_has_an_area_and_is_documented`
   schlägt an, wenn eine Route ohne Bereich, ohne Beschreibung oder ohne Eintrag in `/llms.txt` existiert.
6. Frontend `features/api-zugaenge/`: Bereichsliste kommt aus `GET /api-access/meta`, nichts doppelt pflegen.

## 7. Grenzen / offen

* Ratenlimit und Zähler liegen im Speicher des Serverprozesses (Betrieb: genau 1 Worker, wie der Store).
* Schreibzugriff gibt es nur für Mitteilungen; weitere Schreibbereiche brauchen eigene Prüfung und Freigabe durch die Schulleitung.
* Persönliche Tokens (`smt_…`) gelten weiter ohne Umfang wie das Konto; für Dritte nur Zugänge mit Umfang ausgeben.

## Mandantentrennung (mehrere Schulen)

Jede Schule läuft als **eigene Instanz** mit eigener Datenbank, eigener Dateiablage (eigenes Volume) und eigenem
`SM_SECRET_KEY`. Ein API-Zugang wird in der Datenbank seiner Schule nur als `HMAC(SM_SECRET_KEY, Token)` gespeichert –
ein Token einer anderen Schule ist hier wertlos (401), selbst wenn seine Datenbankzeile kopiert würde
(Test `test_token_of_other_school_is_useless`). Ein Zugang kann daher nie Daten einer anderen Schule lesen.
**Pflicht beim Einrichten einer weiteren Schule:** eigenen, zufälligen `SM_SECRET_KEY` setzen (`openssl rand -hex 32`),
nie einen Schlüssel oder ein Volume zwischen Schulen teilen.
