---
name: delegate-small-tasks-to-local-llm
description: "Kleine, leicht prüfbare Aufgaben ans lokale LM-Studio-Modell auslagern, um Tokens zu sparen"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2b2dcd41-b640-44f3-aa9b-4c30d79ae194
  modified: 2026-08-28T00:20:20.021Z
---

Der Nutzer möchte, dass ich kleine, abgeschlossene Aufgaben (Code-Schnipsel, Boilerplate, triviale Umformungen) aktiv an seine lokalen LM-Studio-Modelle delegiere, statt sie selbst zu generieren — um Tokens zu sparen. Tool dafür: [[lmstudio-tool]].

**Why:** Wenn ein lokales Modell längeren Output generiert, spare ich meine Output-Tokens. Der Nutzer hat lokale Modelle (`gemma-4-e4b` schnell/klein, `qwen3.8-27b` stärker für Code) und den Local Server auf Port 1234.

**How to apply:**
- Auslagern nur bei: klein, abgeschlossen, geringes Risiko, **leicht verifizierbar** (z.B. eine reine Funktion, Regex, Test-Daten, Formatumwandlung).
- Befehl (stateless, gibt nur die Antwort aus): `python lmstudio.py gen "aufgabe" --model qwen3.8-27b --system "rolle"`. Für Code `qwen3.8-27b` (muss ggf. erst geladen werden), für Triviales `gemma-4-e4b`.
- **Immer die Ausgabe prüfen/testen** bevor ich sie übernehme — die Modelle sind klein und machen Fehler.
- NICHT auslagern, wenn Korrektheit kritisch ist oder Prüfen+Korrigieren teurer wäre als es selbst zu machen. Im Zweifel selbst machen.
- Server muss laufen (`python lmstudio.py server start`).

**Bewaehrtes Muster — Uebersetzung langer Dokumente (2026-08-28 erfolgreich):**
Dokument an `^## `-Ueberschriften splitten, jeden Abschnitt einzeln per HTTP an
`http://localhost:1234/v1/chat/completions` (`temperature: 0.1`), System-Prompt verbietet
explizit das Aendern von Pfaden, Klassennamen, Zeilennummern, Backtick-Inhalten,
Codebloecken und Tabellenstruktur. Danach **mechanisch verifizieren**: alle Backtick-Tokens
und Codeblock-Zeilen aus Original und Uebersetzung als Counter vergleichen, plus Anzahl
Ueberschriften und Tabellenzeilen. Ergebnis bei 13 KB Text mit `gemma-4-e4b`: ~100 s,
189/189 Tokens identisch, nur 3 verlorene Backticks und ein paar deutsche Tabellenkoepfe
zum Nachbessern. Das Verifizieren ist billig — genau deshalb eignet sich Uebersetzung gut
zum Auslagern.

**Kalibrierung Code-Review (2026-08-28):** `gemma-4-e4b` als zweites Augenpaar auf unified diffs
funktioniert bei kleinen Patches (10-20 Zeilen) und liefert dort brauchbar "NO ISSUES FOUND".
Bei einem groesseren Diff (~42 Zeilen, EnScript) kam ueber zwei Versuche eine **leere Antwort** —
das ist ein Modellfehler und darf nicht als "sauber" gewertet werden. `qwen3.8-27b-obliterated`
ist fuer Code zwar staerker, brauchte aber >10 min (Laden + Inferenz) und lief in den Timeout.
Fazit: lokale Modelle nur fuer kleine Diffs als Zweitpruefung einplanen, Ergebnis immer daraufhin
pruefen ob ueberhaupt Text zurueckkam, und die eigene Pruefung nie durch sie ersetzen.
