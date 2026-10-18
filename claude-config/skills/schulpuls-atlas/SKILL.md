---
name: schulpuls-atlas
description: >
  MUST USE bei JEDER Arbeit an Schulpuls bzw. Schulmanager (Schul-Manager-Ding, Stundenplan, Vertretung, Klassenbuch, Notenbuch,
  Nachrichten, Kursraeume, Rechte, Login, Datenschutz, Betrieb), am Repo "Claude.Code-merge" oder an dessen Ordnern
  (schulmanager/, frontend/src/, docs/, tests/) - auch fuer Kleinigkeiten wie Knopffarbe aendern, neue Seite, neues Recht, neue
  Migration, neue Benachrichtigung, neuer Import, Bug in einem Fachbereich. Nutzt den externen Code-Atlas
  (C:\Users\reiss\Documents\claude\schulpuls-atlas) zum Nachschlagen von Datei:Zeile, Routen, Tabellen, Tests, Fallstricken,
  BEVOR Quellcode gelesen oder Subagenten gestartet werden. Auch beim Delegieren an Subagenten auf diesem Projekt.
---

# Schulpuls-Atlas: zuerst nachschlagen, dann gezielt lesen

Atlas (extern, nicht im Repo): `C:\Users\reiss\Documents\claude\schulpuls-atlas\`
Generator: `C:\Users\reiss\Documents\claude\tools\schulpuls-atlas\atlas.py` (nur Python-Standardbibliothek, immer mit `python -X utf8`)
Repo (Quelle, nur der Code): `C:\Users\reiss\Documents\claude\Claude.Code-merge`

```
python -X utf8 C:\Users\reiss\Documents\claude\tools\schulpuls-atlas\atlas.py find <begriff> [weitere]   # Treffer in Atlas + Symbolen
python -X utf8 ...\atlas.py update      # nach Code-Aenderungen: maschinelle Teile (Zeilen, Routen, Tabellen, Tests) neu erzeugen
python -X utf8 ...\atlas.py check       # veraltete Zeilen, geloeschte Dateien, Dateien ohne Bereich, tote Notiz-Verweise
python -X utf8 ...\atlas.py selftest    # Selbsttest des Generators
```

**Code-Wissensgraph (Graphify, Standard seit 2026-10-17)**: alle Funktionen, Klassen, Importe, Aufrufe und Docstrings als Graph.
Lokal per tree-sitter, KEINE KI, nichts verlaesst den PC. Liegt im Atlas (`schulpuls-atlas\graph\graphify-out\`), nie im Repo/Image.
Version gepinnt (`uv tool install graphifyy==0.9.74`).
```
G=C:/Users/reiss/Documents/claude/schulpuls-atlas/graph/graphify-out/graph.json
graphify query "<Frage in Worten>" --graph $G --budget 1500   # Wie haengt X zusammen? (Startknoten + Nachbarn mit Datei:Zeile)
graphify explain "<Symbol>" --graph $G                        # ein Symbol mit Aufrufern/Aufgerufenen
graphify path "<A>" "<B>" --graph $G                          # kuerzester Weg zwischen zwei Symbolen (z. B. Route -> Tabelle)
sh C:/Users/reiss/Documents/claude/tools/schulpuls-atlas/graph-update.sh   # nach Code-Aenderungen (inkrementell, ca. 1-2 min)
```
Uebersicht: `graph/graphify-out/GRAPH_REPORT.md` (Gemeinschaften/Kernknoten), `graph.html` (Ansicht im Browser; Gruppen per
`graph_labels.py` ohne KI nach Atlas-Bereichen benannt). Ansicht zeigen: `python -m http.server 8791 --bind 127.0.0.1` im Ordner
`graphify-out` (temporaer, danach stoppen) und `preview_start url=http://127.0.0.1:8791/graph.html`. Fremdcode (Swagger-Bundle,
dist, node_modules) steht in `.graphifyignore` im Repo.

## Ablauf bei jeder Aufgabe

1. **IMMER zuerst den Atlas**, nie sofort Code durchsuchen oder ganze Dateien lesen:
   - `atlas.py find <begriff>` (UND-verknuepft; Symbol `Scheduler.check`, CSS-Klasse `.btn-primary`, Token `--primary`, Route `/notifications`, Tabelle, Recht `gradebook.export`).
   - `INDEX.md` (Bereichsliste) und die passende Bereichsdatei `features/<bereich>.md`: Dateien mit Symbolen und Zeilen, Routen mit Recht, Tabellen und Migrationen, Frontend-Routen, CSS-Klassen, Tests samt Befehl, Abhaengigkeiten, **Fallstricke** (unter `<!-- eigene Notizen -->`).
   - Wiederkehrende Aufgaben: `design/rezepte.md` (Knopffarbe, neue Seite, neues Recht, neue Migration, neue Benachrichtigung, Loeschkonzept, Notenbuch-Quelle, Abschlussbedingung, Import). Gestaltungsregeln: `design/regeln.md`, Raster: `design/raster.md`, Tokens: `design/tokens.md`.
   - Weitere Verzeichnisse: `api/routes.md`, `db/tables.md`, `db/migrations.md`, `frontend/routes.md`, `frontend/components.md`, `tests/map.md`, `symbols.tsv`.
2. **Dann nur die genannten Abschnitte** der Dateien lesen (Datei:Zeile, ca. +-60 Zeilen), nicht die ganze Datei.
3. Ausfuehrliche Prosa der frueheren Code-Doku (Paragraphen-Verweise wie "03 §6"): `doku/code/0N-*.md`, `doku/code/README.md`. Interne Entwicklerdoku, Recherchen: `doku/intern/`.
4. **Nach Code-Aenderungen (Pflicht: alles bleibt dokumentiert)** `atlas.py update`, `atlas.py check` UND `graph-update.sh`
   ausfuehren; neue Funktionen/Klassen bekommen einen kurzen deutschen Docstring (wird Knotentext im Graphen). Bei Subagenten
   diese Schritte in den Auftrag schreiben. Neue Fallstricke, neue Bereiche, geaenderte Regeln in die Bereichsdatei unterhalb von `<!-- eigene Notizen -->` schreiben (Text oberhalb der Markierung ueberschreibt der Generator). Neue Datei ohne Bereich: Muster in `areas.json` des Atlas ergaenzen (`check` meldet "OHNE BEREICH"). Handnotizen duerfen Dateinamen in Backticks nennen; `check` prueft, dass es sie gibt.
5. **Subagenten**: im Prompt den Atlas-Pfad und die relevante Bereichsdatei nennen ("Lies zuerst `C:\Users\reiss\Documents\claude\schulpuls-atlas\INDEX.md` und `features/<bereich>.md`, nutze `atlas.py find`, lies nur die genannten Abschnitte"), die Dateihoheit festlegen (welche Dateien geaendert werden duerfen), "nur Tests der geaenderten Bereiche, kein Gesamtlauf", "nicht committen". Keine Keys/Passwoerter/.env in Prompts.
6. Der Atlas ist bewusst **ausserhalb des Repos** und gehoert nicht in Images, Backups oder Weitergaben an Kunden (Schutz des Codes, siehe `SCHUTZ-DES-CODES.md`). Nichts daraus ins Repo kopieren.

## Projektregeln (Kurzfassung, Details `design/regeln.md`)

- **Sie-Form fuer alle**, auch Schueler/innen (Entscheidung des Nutzers 2026-10-16, nie "du"); keine KI-Erklaerabsaetze, keine Emojis; Produktname nur ueber `APP_NAME` (`frontend/src/brand.ts`) bzw. `PRODUCT_NAME` (`schulmanager/branding.py`).
- **Ein Raster fuer alles**: jede Ansicht Tage x Stunden nutzt `components/grid/DayPeriodGrid.tsx` (TimetableGrid), nie ein neues Raster.
- **HelpTip/Hilfe statt Erklaertext**: Erklaerungen als `Field help=`, `HelpText`, `PageHelp`, `HelpTip`; `className="explain"` ist per `designRules.test.ts` gedeckelt (nur senken).
- **"Nachrichten" ist ein Menueeintrag** (Postfach, Chats, Rundschreiben, Mails, Mitteilungen in einer Liste).
- Farben nur ueber Tokens; dunkles Schema steht zweimal in `tokens.css`; Rechte und Datenumfang im Backend pruefen, fremde Daten 404; jede schreibende Aktion `audit()`; Planungsdokument nur ueber `mutate`; Schema nur per Alembic.
- **Keine Server auf dem PC starten.** Deploy nur auf den Heimserver (Rezept im Projekt-Gedaechtnis `schulmanager-deploy`).
- **Nicht committen/pushen ohne Auftrag**; kein `git checkout/stash/reset/clean` im Arbeitsbaum (viel ist uncommittet, Agenten arbeiten parallel).
- **Prettier nie mit Standardwerten** auf bestehende Dateien anwenden.
- **Nur die Tests der geaenderten Bereiche** laufen lassen (Befehle je Bereich in `tests/map.md` bzw. Bereichsdatei); der Gesamtlauf (Backend + Frontend) genau einmal vor dem Deploy.
- `ask-cheap` (siehe globale Regeln) fuer lange Ausgaben, Zusammenfassungen, Boilerplate nutzen; nie Keys/Kundendaten senden.
