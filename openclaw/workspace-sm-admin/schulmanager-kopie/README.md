# Schulpuls – Stundenplan & Live-Vertretungsplan

> **Produktname: Schulpuls** (intern weiter `schulmanager`: Python-Paket, `SM_*`-Variablen, Cookies, Docker, Routen).
> Marke zentral in `frontend/src/brand.ts` und `schulmanager/branding.py`; Logo und Begründung: `docs/branding/`.

Vollständige Schulverwaltung (Full-Stack) für große Schulen – ausgelegt auf **~2500 Schüler, mehrere hundert
Lehrkräfte und zwei Standorte**. Kern ist ein automatischer Stundenplan-Generator und eine
Live-Vertretungsplanung, die bei Krankmeldungen sofort umplant und Ausfall **an den Rand des Schultags** legt.

> Status: lauffähige erste Version (siehe „Grenzen & nächste Schritte“). Entwickelt von einem Team aus
> KI-Agenten mit gemeinsamem Architektur-Vertrag (`docs/ARCHITECTURE.md`) und geteiltem Gedächtnis
> (`docs/AGENT_NOTES.md`).

## Funktionen

### Stundenplanung
- **Stundentafeln**: pro Jahrgang oder einzelne Klasse festlegen, welche Fächer mit wie vielen Wochenstunden
  stattfinden müssen (inkl. Doppelstunden-Wunsch).
- **Automatischer Generator** (Konstruktion → Verdrängungsreparatur → Simulated Annealing, mehrere CPU-Kerne parallel):
  keine Doppelbelegungen von Klassen/Lehrkräften/Räumen, Fachräume (Chemie, Sporthalle …), Kopplungen
  (Religion/Ethik parallel, Oberstufen-Schienen), Deputate, Sperrzeiten.
- **Prioritäten/Gewichte** einstellbar: Hohlstunden der Klassen vermeiden, Springstunden der Lehrkräfte,
  Hauptfächer früh am Tag, gleichmäßige Tage, Fächer über die Woche verteilt, Standortwechsel minimieren,
  Lehrerwünsche (weich) …
- **52-Wochen-System**: Alle Wochen des Schuljahres zählen durch (Woche 1 bis 52/53, Ferien zählen mit), jede Woche
  hat 7 Tage. Alles, was nicht jede Woche gilt (Kurse, Sperrzeiten, Wünsche, Zeitfenster, Aufsichten …), gilt **jede
  Woche**, in **ausgewählten Wochen** oder im **Rhythmus** („alle k Wochen ab Woche s, optional bis Woche e“, k
  beliebig). Klassen, die z. B. *jeden Mittwoch* (Praxistag) oder *jede 2. Woche mittwochs* (Berufsschule) nicht da
  sind, werden korrekt verplant; Unterrichtstage je Klasse (auch Sa/So). Ältere Planungsdokumente mit Wochenzyklus
  werden beim Laden verlustfrei auf Rhythmen umgerechnet.
- **Zwei (oder mehr) Standorte**: Räume und Klassen gehören zu Standorten; Lehrkräfte **und** Klassen bekommen
  zwischen Standortwechseln die nötige Wegezeit; Lehrkräfte werden möglichst standorttreu eingesetzt.
- **Manuell nachbessern**: Stunden per Drag & Drop verschieben (gültige Ziele werden angezeigt, Konflikte erklärt,
  Räume automatisch getauscht), Stunden fixieren und den Rest neu generieren lassen.
- **Qualitätsbericht**: fehlende Stunden, Hohlstunden, Springstunden, Deputatsüberschreitungen, Konflikte.

### Live-Vertretungsplan
- Krankmeldung erfassen (Sekretariat/Planer) oder **selbst melden** (Lehrkraft) → Plan wird sofort neu berechnet und
  per Live-Update (Server-Sent Events) an alle offenen Geräte, den Flur-Monitor, Webhooks und per E-Mail verteilt.
- **Ausfall nur am Rand**: Ab einer einstellbaren Klassenstufe entfallen betroffene Rand-Stunden; Lücken in der
  Tagesmitte werden zuerst durch **Verlegung** einer Randstunde geschlossen, sonst vertreten. Jüngere Klassen
  werden immer vertreten/betreut.
- Vertretungsvorschläge mit Begründung (fachlich passend, kennt die Klasse, hat ohnehin eine Freistunde, ist durch
  Klassenfahrt frei geworden, gleicher Standort, faire Verteilung), manuelle Übersteuerung jederzeit.
- Klassen-Abwesenheiten (Exkursion), Raumsperrungen, Teil-Abwesenheiten, Ferien/Feiertage, Klausuren, Pausenaufsichten.
- **Klassen-Seite**: Klasse suchen → Schüler/innen, Klassenleitung, Fachlehrkräfte je Fach, Klassenraum (direkt änderbar)
  und Wochenplan einer Kalenderwoche mit allen Änderungen. Dort eine Stunde als **„findet nicht statt“** markieren oder
  „Klasse ist nicht da“ (Ausflug, mit Begleitlehrkräften) – mit Vorschau; das System stellt automatisch um (Randstunde
  vorziehen, Entfall am Rand, Betreuung jüngerer Klassen, frei gewordene Lehrkräfte vertreten).
- **Konten & Anmeldung**: E-Mail/Handy bestätigen und „Passwort vergessen“ per E-Mail/SMS; neue Klassen mit
  Schülerliste, Eltern und automatischen Zugangsbriefen als PDF (einzeln, ZIP, per E-Mail), Startpasswort
  wiederherstellen oder selbst setzen (auch Klassenleitung); Anmeldung mit Microsoft, Apple, Google oder Schulkonto;
  Anmelde-Richtlinien je Person, Klasse (Schüler/innen oder Eltern), Jahrgang und Rolle inkl. Pflicht-Verknüpfungen.

### Konten & Rollen (serverseitig)
Admin · Schulleitung · Stundenplaner · Sekretariat · Lehrkraft · Schüler · Eltern · Monitor – mit Rechtematrix,
sicheren Passwörtern (scrypt), Sitzungen, CSRF-Schutz, 2-Faktor-Anmeldung (TOTP), Sperre bei Fehlversuchen,
Massenanlage von Schüler-/Eltern-/Lehrerkonten mit druckbaren Zugangsbriefen, API-Tokens für Integrationen,
persönliche Kalender-Abos (iCal), Änderungsprotokoll mit Undo, DSGVO-Datenexport.

### Lehrkräfte, Kursräume, Postfach, Schüler & Eltern
- **Lehrer-Selbstverwaltung**: Jede Lehrkraft pflegt im eigenen Konto Fächer, Klassen, die sie hauptsächlich unterrichtet,
  Deputat und **Arbeitszeitfenster** (z. B. „erst ab 10:00“ oder „nur Abendunterricht ab 16:00“). Je nach Einstellung
  gilt das sofort oder nach Genehmigung; der Stundenplan der Lehrkraft lässt sich danach gezielt neu planen.
  Lehrkräfte melden sich selbst krank und sehen **nur ihre Fächer, Kurse und Klassen** – keinen Vollzugriff.
- **Kursräume** (Moodle-ähnlich, eigene Umsetzung): je Kurs/Klasse Ordner mit Material, Freigabe **zu einer bestimmten
  Unterrichtsstunde** für die angemeldeten Schüler/innen, Aufgaben mit Abgabe und Rückmeldung, Pinnwand.
- **Internes Postfach** für alle Rollen (Einzel- und Gruppennachrichten, Anhänge, Melden/Moderation, Blockieren) –
  Inhalte und Dateien **verschlüsselt** gespeichert.
- **Meine Übersicht** für Schüler/innen und Eltern (je Kind): Stundenplan heute/nächster Schultag, Klausuren, offene
  Aufgaben, Nachrichten, **Krankmeldung mit einem Klick** – selbst, wenn die Schule das Konto als volljährig markiert hat,
  sonst durch die Eltern. **Atteste und andere Dokumente** werden hochgeladen; ab N Schultagen erscheint „Attest fehlt“.
  Atteste sehen nur Sekretariat, Schulleitung und Klassenleitung – nie Fachlehrkräfte.

### Zusammenarbeit mit anderen Systemen
- **Untis** (GPU-Dateien: Stundenplan, Unterricht, Klassen, Lehrer, Räume, Fächer, Schüler, Vertretungen) – Import & Export
- **Schulmanager Online** und ähnliche Plattformen: Export-Paket (dateibasierter Import, Anleitung im Paket)
- **SchILD-NRW / ASV / CSV** (Excel-kompatibel, Spalten-Mapping)
- **iCal-Feeds** für Handy-Kalender, **REST-API** mit Tokens, **signierte Webhooks**

## Schnellstart

Ausführliche Betriebsanleitung: [`docs/BETRIEB.md`](docs/BETRIEB.md), Sicherheit/DSGVO: [`docs/SICHERHEIT.md`](docs/SICHERHEIT.md),
Architektur: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

### Vorschau im Browser (GitHub Codespaces)

[![In GitHub Codespaces öffnen](https://github.com/codespaces/badge.svg)](https://codespaces.new/L0rdr3spawn/Claude.Code/tree/claude/magical-newton-dcni3v?quickstart=1)

Ein Klick startet die komplette App mit Demo-Schule in einem privaten Codespace (erster Start einige Minuten) und öffnet
sie im Browser – auch am Tablet oder Handy nutzbar. Konten und ein Rundgang zum Ausprobieren: [`docs/VORSCHAU.md`](docs/VORSCHAU.md).
Lokal genügt nach der Installation `scripts/preview.sh` (→ http://localhost:8000).

### Ausprobieren mit Demo-Schule (lokal)

```bash
make install        # Python-Umgebung + npm-Pakete
make demo           # frische Datenbank, Demo-Schule (≈2600 Schüler) wird beim Start generiert
# Backend: http://localhost:8000  ·  Frontend (Hot-Reload): http://localhost:5173
```

Ohne `make`:

```bash
pip install -e ".[dev]"
(cd frontend && npm ci && npm run build)
SM_LOAD_DEMO=1 uvicorn schulmanager.server.app:app --port 8000   # → http://localhost:8000
```

Die Demo erzeugt eine Gesamtschule mit zwei Standorten, Rhythmus-Beispielen, Praxisklassen (jeden Mittwoch
weg), Berufsschul-Kooperationsklassen (jede 2. Woche ab Woche 1 Mi, jede 2. Woche ab Woche 2 Di+Do weg) und Oberstufe mit Kursschienen.

| Konto | Rolle | Passwort (nur Entwicklung) |
|---|---|---|
| `admin` | Administrator | `admin12345` (Wechsel beim ersten Login) |
| `schulleitung`, `planer`, `sekretariat` | Leitung / Stundenplanung / Sekretariat | `demo123456` |
| `lehrer1` … `lehrer3` | Lehrkräfte | `demo123456` |
| `schueler1` (Jg. 5), `schueler2` (Praxisklasse), `schueler3` (Oberstufe, volljährig, Klasse von `lehrer1`), `schueler4` (Kurs von `lehrer1`) | Schüler | `demo123456` |
| `eltern1` (zwei Kinder) | Eltern | `demo123456` |
| `monitor` | Flur-Monitor (`/monitor/S1`) | `demo123456` |

### Produktion (Docker)

```bash
cp .env.example .env    # Domain, Passwörter, SM_SECRET_KEY (openssl rand -hex 32) eintragen
make up                 # App + PostgreSQL + Caddy (automatisches HTTPS) + nächtliche Backups
docker compose exec app python -m schulmanager.server.cli create-admin --username admin
make monitoring-up      # optional: Prometheus + Grafana
```

Betriebs-CLI: `python -m schulmanager.server.cli {migrate|create-admin|reset-password|unlock|disable-2fa|list-users|load-demo|backup|maintenance}`.

### Typischer Ablauf für ein neues Schuljahr

1. **Stammdaten** anlegen oder importieren (CSV aus SchILD/ASV, Untis-GPU): Standorte, Räume, Fächer, Lehrkräfte
   (Fächer, Deputat, Sperrzeiten, Wünsche), Klassen (inkl. Rhythmus-Regeln), Schüler.
2. **Planung → Stundentafeln**: Fächer und Wochenstunden je Jahrgang/Klasse; Kopplungen (Religion, Oberstufe) unter *Kurse*.
3. **Kurse erzeugen → Lehrkräfte zuweisen → Generator** (30–300 s, nutzt alle Kerne) → Bericht prüfen → *Übernehmen*.
4. Nachbessern per Drag & Drop, Stunden fixieren, erneut generieren.
5. **Benutzer → Massenanlage**: Konten für Schüler, Eltern und Lehrkräfte, Zugangsbriefe drucken.
6. Im Schulalltag: Krankmeldungen erfassen bzw. von Lehrkräften selbst melden lassen – der Vertretungsplan
   aktualisiert sich live auf allen Geräten und dem Flur-Monitor; Export nach Untis/Schulmanager Online bei Bedarf.

## Projektstruktur

| Pfad | Inhalt |
|---|---|
| `schulmanager/models.py` | Datenmodell (Klassen, Lehrkräfte, Räume, Stundentafeln, Kurse, Rhythmusregeln, Standorte …) |
| `schulmanager/scheduler.py` | Stundenplan-Generator |
| `schulmanager/planning.py` | Stundentafel → Kurse, Lehrerzuweisung, Kapazitätsprüfung |
| `schulmanager/timetable.py` | Ansichten, Verschieben, Qualitätsbericht |
| `schulmanager/substitution.py` | Vertretungsplan-Engine |
| `schulmanager/duties.py`, `exams.py` | Pausenaufsichten, Klausuren |
| `schulmanager/teacher_profile.py`, `channels.py`, `messaging.py`, `student_self.py` | Lehrer-Selbstverwaltung, Kursräume, Postfach, Krankmeldungen/Atteste (reine Logik) |
| `schulmanager/integrations/` | Untis, Schulmanager Online, CSV, iCal, Webhooks |
| `schulmanager/server/` | FastAPI-Server: Konten, Rechte, Datenbank, API, Live-Events, Verschlüsselung (`crypto.py`), Dateiablage (`files.py`) |
| `frontend/` | Web-Oberfläche (React + TypeScript); Erweiterungen als Feature-Module in `frontend/src/features/` |
| `deploy/`, `Dockerfile`, `docker-compose.yml` | Betrieb |
| `docs/` | Architektur, Betrieb, Sicherheit |

## Tests

```bash
make test     # ≈350 Python-Tests (pytest) + ≈100 Frontend-Tests (vitest)
make lint     # ruff, TypeScript, shellcheck, compose config
```

## Grenzen & nächste Schritte

- Ein App-Prozess pro Installation (Live-Events und Arbeitskopie des Plans liegen im Speicher) – für eine Schule
  mit 2500 Schülern reicht das deutlich (Messung: „Mein Tag“ 4–13 ms, Tages-Vertretungsplan 15–40 ms).
- Der Generator ist eine Heuristik: Er findet gute, aber nicht beweisbar optimale Pläne; mehr Rechenzeit → weniger Hohlstunden.
- Untis-GPU-Spaltenbelegungen sind nach öffentlich verfügbaren Quellen umgesetzt und im Code als sicher/unsicher markiert –
  vor dem ersten Produktivimport mit einem Testexport der eigenen Untis-Version abgleichen.
- Schulmanager Online bietet keine öffentlich dokumentierte API; die Anbindung erfolgt dateibasiert (Export-Paket mit Anleitung).
- Verlegungen im Vertretungsplan erfolgen innerhalb desselben Tages und nur für Einzelstunden.
