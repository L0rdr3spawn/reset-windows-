# Globale Regeln

## ask-cheap: Routinearbeit an günstige KI abgeben

`ask-cheap` (in `~/.local/bin`) schickt Prompts an kostenlose LLM-APIs (aktuell Groq `gpt-oss-120b`, Fallback Gemini/OpenRouter, sobald Keys da sind). Ziel: Claude-Usage sparen. Der User will, dass es **proaktiv bei allem mitläuft**, wo es passt – nicht erst auf Nachfrage.

**Zuerst `ask-cheap` nutzen für:**
- Lange Ausgaben zusammenfassen, von denen nur das Wesentliche gebraucht wird: Logs, Build-/Test-Output, lange Dokus, Diffs, Webseiten-Text (`befehl > out.txt; ask-cheap "Fasse die Fehler zusammen" --files out.txt`)
- Übersetzungen, Umformulieren, Textentwürfe (Mails, READMEs, Kommentare)
- Boilerplate und erste Code-Entwürfe für klar umrissene Funktionen – danach selbst prüfen und ausführen
- Daten aus Text extrahieren (JSON, Listen, Tabellen)
- Viele Dateien gleichartig bearbeiten: `ask-cheap "…" --files a b c --parallel 3`
- Zweitmeinung bzw. Ideen sammeln
- Kurze Web-Recherche mit `--web` (nur Groq, ~8k Tokens pro Anfrage). Ergebnisse waren im Test teils veraltet → immer anhand der ausgegebenen Quellen prüfen, für Wichtiges selbst recherchieren.

**Nicht nutzen / niemals senden:**
- Keys, Passwörter, Tokens, `.env`-Inhalte, private Daten, Kundendaten, Diktate/Aufnahmen des Users (Free Tiers dürfen Daten speichern bzw. zum Training nutzen)
- Aufgaben, die Tools, Dateizugriff oder genaues Verständnis des ganzen Projekts brauchen – das bleibt bei Claude
- Endgültige Entscheidungen, Sicherheits- oder Architekturfragen

**Ergebnisse prüfen:** Fakten aus gegebenem Text waren im Test zuverlässig (Logs 7/7, Code 18/18 Tests, JSON korrekt). Eigene Deutungen/Ursachen-Schlüsse waren teils falsch (zeitlich unmöglich) → Fakten übernehmen, Interpretation selbst machen. Code immer ausführen/testen.

**Bedienung (Claude Code):**
- Ohne Pipe immer `--no-stdin` setzen (sonst 3 s Wartezeit auf eine stumme stdin-Pipe).
- Pipen geht: `cat datei | ask-cheap "Prompt"`. Bei langsamen Befehlen erst in eine Datei schreiben, dann `--files` (oder `--stdin`).
- Limit Groq Free: ~8.000 Tokens/Minute → Eingaben über ~300 Log-Zeilen bzw. ~20 KB aufteilen (z. B. `split`), sonst HTTP 413. Mehrere Aufrufe hintereinander können je bis ~30 s warten.
- `-v` zeigt Anbieter/Modell, `--fast` für einfache Aufgaben, `--system ""` schaltet die Knapp-Vorgabe ab, `ask-cheap --test` prüft die Keys.
- Wenn `ask-cheap` fehlschlägt (kein Anbieter, Limit), einfach selbst weitermachen.
- Dem User kurz sagen, wenn ein Teil per `ask-cheap` erledigt wurde.

Keys trägt nur der User selbst ein (Desktop-Verknüpfung `API-Keys` → Fenster `~/.local/bin/api-keys.pyw`). Nie Keys in den Chat holen oder selbst speichern. Groq: zwei Accounts (`groq`, `groq2`) auf Wunsch des Users – `ask-cheap` verteilt automatisch und wechselt bei Limit sofort; `ask-cheap --status` zeigt das Restbudget. Weitere Accounts nur, wenn der User es ausdrücklich will.
