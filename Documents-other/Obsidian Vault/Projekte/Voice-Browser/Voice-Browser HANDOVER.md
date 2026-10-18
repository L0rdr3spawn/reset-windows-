# Übergabe – Jev Voice Browser

Stand: **2026-09-20** (Flow-Diktat nachts, danach die Punkte 1, 2 und 4 der vorigen Übergabe).
Diese Datei sagt, **wo das Projekt gerade steht** und **wie man weitermacht**.
Was das Projekt kann und wie man es bedient, steht in [README.md](README.md) – hier steht es nicht noch einmal.

---

## 1. In fünf Minuten wieder am Laufen

```bat
start.cmd
```

Das startet `server.py` auf `127.0.0.1:8765`, hängt den Diktat-Hotkey ein (rechte Strg) und zeigt
das Overlay. Danach:

1. Edge öffnen → Seitenleiste (Jev-Symbol oder `Alt+Shift+V`). Die Erweiterung liegt entpackt in
   `extension/` und muss nach jedem Codeänderung in `edge://extensions` **neu geladen** werden.
2. Mikrofon: einmal `mic.html` in einem Tab erlauben (Seitenleiste → Einstellungen → Mikrofon).
3. Prüfen, ob der Server antwortet: `curl http://127.0.0.1:8765/health`

Ohne Fenster / ohne Hotkey: `python server.py --no-overlay --no-flow`.

**Was sonst noch laufen muss:**

| Für | Braucht |
| --- | --- |
| Alles (Befehle verstehen) | `TYPESAFE_API_KEY` – Env, Registry (`HKCU\Environment`) oder `../cs2-jev/.env` |
| Spracherkennung | Edge + Internet (Brave/Chrome haben `webkitSpeechRecognition` nicht) |
| Textglättung beim Diktat, Zusammenfassen, Fragen zur Seite | LM Studio auf `127.0.0.1:1234` (optional, siehe `../lmstudio.py`) |

---

## 2. Woran zuletzt gearbeitet wurde

Davor war das **Flow-Diktat** (Taste halten → sprechen → Text landet im aktiven Programm) der
letzte Baustein. Zwei Dinge daran waren die eigentliche Arbeit und sollten nicht wieder
kaputtgehen:

* Das Overlay läuft im **Hauptthread**, der HTTP-Dienst im Nebenthread (Tkinter erzwingt das).
* Das Overlay-Fenster hat `WS_EX_NOACTIVATE`, sonst klaut es den Fokus und der diktierte Text
  landet im falschen Programm.

Zuletzt wurden die offenen Punkte 1, 2 und 4 der vorigen Übergabe abgearbeitet:

* **`--test` ist jetzt ein Trockenlauf.** `python server.py --test "…"` ruft `interpret()` mit
  `dryRun` auf und fasst den PC nicht mehr an; `--echt` führt wirklich aus.
* **Groß-/Kleinschreibung.** Die Textaufbereitung in `flow.py` ist in Stufen zerlegt
  (`apply_dictionary`, `sentence_case`, `keep_capitals`) und die LLM-Antwort läuft jetzt durch
  `flow.polish()`: Wörterbuch erneut anwenden, Satzanfänge geraderücken und jede Großschreibung
  nachziehen, die in Stufe 1 schon **mitten im Satz** stand. Satzanfänge der Referenz zählen
  dabei nicht (sonst würde jedes „Das“ mitten im Satz großgezogen), und Wörter, die in der
  Referenz auch klein vorkommen, bleiben unangetastet. Dazu: `temperature: 0` für die Glättung
  und ein Beispiel im Prompt – kleine Modelle folgen einem Beispiel besser als einer Regel.
* **Gegenprobe vor folgenreichen Aktionen** (der geplante Punkt „Bewertung vor der Ausführung“).
  `server.gegenprobe()` stellt Jev eine zweite, unabhängige Noul-Frage, die nur noch die
  getroffene Wahl kennt: „wollte der Nutzer genau das, und darf es ohne Rückfrage passieren?“
  Unter 0,7 wird gefragt statt ausgeführt. Nur für `server.FOLGENREICH`, weil es ~0,6 s kostet.

**Warum keine Substantiv-Regel im Code:** eine Regel „Artikel + nächstes Wort → groß“ trifft
„ein test“ → „ein Test“, aber genauso „der schnelle hund“ → „der Schnelle hund“. Attributive
Adjektive lassen sich ohne Wortliste nicht von Substantiven trennen, deshalb bleibt die
Substantiv-Großschreibung beim Modell – der Code zieht nur nach, was er sicher weiß.

---

## 3. Was geprüft ist – und was nicht

**Geprüft:**

* `python test_text.py` – Textaufbereitung ohne API und ohne LM Studio, zuletzt **16/16**.
  Schnell und kostenlos; das ist der Test, den man nach jeder Änderung an `flow.py` laufen lässt.
* `python eval.py` – 55 Beispieläußerungen und 6 App-Auswahlen gegen die echte Jev-API,
  zuletzt **55/55 und 6/6** (nach dem Umbau erneut gelaufen). Läuft mit `dryRun`.
* Gegenprobe von Hand: „sperr den pc“ 0,88 · „drück alt f4“ 0,81 · „schließ das fenster von
  spotify“ 0,86 gehen durch; „drück steuerung alt entfernen“ 0,17 → Rückfrage.
* Befehle im Browser und auf dem Desktop: über 400 Zeilen in `log.jsonl`, Antwortzeit meist
  0,8–0,9 s (mit Gegenprobe 1,4–1,5 s).
* Diktat im eigenen Testfenster.
* Neuer Glättungs-Prompt gegen `gemma-4-e4b`, fünf Diktate: Substantive kamen in allen fünf
  richtig groß („Test des Overlays“, „Termin am Montag“, „die Datei“, „den Code“). Bei
  „das war ne blöde idee nein lieber machen wir es morgen“ warf das Modell den ersten Halbsatz
  ganz weg – die vorhandene Treue-Prüfung gab dafür 0,06 und hat Stufe 1 eingefügt. Der
  Sicherheitsnetz-Weg ist also nachweislich der, der greift, wenn die Glättung übertreibt.
* Achtung bei der Zeitmessung: kaltes bzw. gerade umgeladenes Modell brauchte 9–11 s, warmes
  0,4–0,5 s. Mit `cleanup_wait` = 1,5 s heißt das: kalt gibt es Stufe 1, warm die Glättung.

**Nicht geprüft / offen:**

* Diktat in **fremden Programmen** (Discord, Word, Code) – bisher nur im eigenen Testfenster.
  Der Tastatur-Hook ignoriert selbst gesendete Tasten (`LLKHF_INJECTED`), deshalb war das
  Testfenster nötig; zum Nachstellen gibt es `allow_injected` in `flow_config.json`.
* Dauerbetrieb: ob der Hook nach Standby/Benutzerwechsel noch hängt, wurde nie beobachtet.

---

## 4. Offene Punkte

1. **Diktat in echten Programmen** durchspielen (Discord, Word, Code): Server starten, in das
   fremde Programm klicken, Taste halten, sprechen. Offen ist dabei nicht mehr der Text – der
   ist oben gegen das Modell geprüft –, sondern der Weg dorthin: greift der Hook, wenn ein
   anderes Programm vorn ist, kommt der Fokus über `refocus()` zurück, und überlebt die
   Zwischenablage das Einfügen? Das geht nur am echten Rechner.
2. **Schwelle der Gegenprobe** (0,7, `server.GEGENPROBE_SCHWELLE`) ist geschätzt, nicht
   gemessen. Nach ein paar Tagen `log.jsonl` nach `gegenprobe` filtern und schauen, ob sie zu
   oft oder zu selten fragt. Ebenso die Liste `server.FOLGENREICH` – `text_tippen_pc` ist
   bewusst **nicht** drin, weil Tippen mit Strg+Z zurückzunehmen ist und kein Enter folgt.
3. **`log.jsonl` wächst ungebremst** (120 KB). Irgendwann rotieren.

---

## 5. Stolperfallen (kosten sonst Stunden)

* **ctypes braucht Prototypen** (`restype`/`argtypes`) für alles mit Handles. Ohne sie kürzt Python
  64-Bit-Handles auf 32 Bit: `SetWindowsHookExW` scheitert mit Fehler 126, und die Zwischenablage
  (`GlobalAlloc`/`GlobalLock`) lässt den Prozess mit Segfault abstürzen.
* **Erweiterung nach jeder Änderung neu laden**, sonst läuft der alte Code weiter.
* **`msedge.exe --version` startet den Browser** – zum Testen Edge mit eigenem `--user-data-dir`,
  `--load-extension` und `--remote-debugging-port` starten und `sidepanel.html?tab=<tabId>` als
  Popup öffnen (Testmodus im Code, Befehle lassen sich eintippen).
* **Die Seitenleiste darf selbst nicht nach dem Mikrofon fragen** – dafür ist `mic.html` da.
* Freie Werte (Suchtext, Diktat) werden **nie generiert**, sondern als Wortabschnitt der Äußerung
  ausgewählt. Wer das ändert, verliert die Garantie, dass nichts erfunden wird.

---

## 6. Wenn etwas nicht tut

| Symptom | Zuerst hier schauen |
| --- | --- |
| Befehl wird falsch verstanden | `log.jsonl` – jede Äußerung mit erkannter Aktion, Konfidenz und Alternativen |
| Aktion fehlt oder Schwelle passt nicht | `intents.py` (Katalog, Kandidaten, Policy) |
| Ganze Erkennung prüfen | `python eval.py` (echte API) |
| Diktattext falsch aufbereitet | `python test_text.py` (offline, kostenlos) |
| Aktion wird unnötig nachgefragt | `gegenprobe` in `log.jsonl`, Schwelle in `server.py` |
| Diktat reagiert nicht | Läuft der Server? Hook aktiv? → `curl http://127.0.0.1:8765/flow/state` |
| Text landet im falschen Fenster | Overlay-Fokus (`WS_EX_NOACTIVATE` in `overlay.py`) |

---

## 7. Verwandte Notizen

* `../jev.py` – dasselbe Jev-Muster als kleines CLI (`route`, `check`, `choice`, `noul`, `score`).
* `../lmstudio.py` – lokales LM Studio, wird für Glättung, Zusammenfassung und Seitenfragen genutzt.
* `../cs2-jev/coach.py` – zweites Jev-Projekt, gleiches Muster (Regeln im Code, Urteile von Jev).
