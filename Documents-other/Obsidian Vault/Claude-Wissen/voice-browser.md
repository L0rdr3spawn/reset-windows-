---
name: voice-browser
description: "Jev Voice Browser unter voice-browser/ - Sprachsteuerung für Edge UND Windows; Edge ist das Mikrofon, weil Brave keine Spracherkennung hat"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3bbdb336-2e92-4621-b402-3e7d62f6a7d0
  modified: 2026-09-19T23:46:40.016Z
---

`C:\Users\reiss\Documents\claude\voice-browser\` (seit 2026-09-19/20): Sprachsteuerung für Browser
und Windows. Aufbau: Edge-Seitenleisten-Erweiterung (`extension/`) hört zu und spricht,
`server.py` (nur Standardbibliothek, Port 8765) fragt Jev und führt Windows-Aktionen aus,
`desktop.py` macht Tastatur (SendInput), Fenster (user32) und Apps (`Get-StartApps`).

**Why:** Wunsch des Users; nutzt [[jev-im-workflow]] und [[typesafe-skill]] produktiv – eine
Jev-Anfrage pro Befehl mit parallelen Fragen (Aktion + Textabschnitt + Element + Fenster + Tab +
Ordner + Einstellung + "heikel?"-Noul), ~0,7–1,0 s. Freie Werte werden nie generiert, sondern als
Wortabschnitt der Äußerung bzw. aus Listen ausgewählt.

**Flow-Diktat (wie Wispr Flow, seit 2026-09-20):** `flow.py` hängt einen globalen
WH_KEYBOARD_LL-Hook ein: rechte Strg halten → sprechen → loslassen → geglätteter Text wird per
Zwischenablage ins aktive Programm eingefügt (~1,8 s). Jev entscheidet pro Aufnahme
diktat/befehl/korrektur/verwerfen und prüft per Noul, ob die LLM-Glättung dasselbe sagt – sonst
wird die einfache Code-Bereinigung eingefügt. Die Seitenleiste hört standardmäßig NUR während der
gedrückten Taste zu (Schalter „flowOnly").

Overlay: `overlay.py` (Tkinter-Pille unten mittig, Pegelbalken, Live-Text) läuft im HAUPT-Thread,
der HTTP-Dienst daneben im Thread. Taste umstellbar in der Seitenleiste oder `flow_config.json`
(`rctrl`, `capslock`, `f9`, auch `ctrl+alt+d`), wirkt sofort. Die LLM-Glättung ist optional
(`cleanup: false`) – ohne sie braucht Flow kein LM Studio.

**Nicht offensichtliche Fakten:**
- Overlay-Fenster braucht `WS_EX_NOACTIVATE`, sonst klaut es den Fokus und der Text wird ins
  falsche Fenster eingefügt.
- **ctypes braucht Prototypen** (`restype`/`argtypes`) für alles mit Handles: ohne sie kürzt Python
  64-Bit-Handles auf 32 Bit → `SetWindowsHookExW` schlägt mit Fehler 126 fehl und die
  Zwischenablage (`GlobalAlloc`/`GlobalLock`) lässt den Prozess mit Segfault abstürzen.
- Der Hook ignoriert selbst gesendete Tasten (`LLKHF_INJECTED`); zum Testen gibt es
  `allow_injected` in `flow_config.json`. Testfenster: eigenes Tkinter-Fenster statt fremder Apps.
- **Brave und Chrome haben kein `webkitSpeechRecognition`** (nur Edge, über Microsofts Dienst, mit
  Internet). Deshalb ist Edge das "Ohr", auch wenn der User sonst Brave benutzt. In allen anderen
  Programmen wirken Browser-Befehle über Tastenkürzel (`DESKTOP_EQUIV` in `intents.py`).
- Die Seitenleiste darf selbst nicht nach dem Mikrofon fragen → einmal `mic.html` in einem Tab
  öffnen und erlauben; dieselbe Seite kann notfalls stellvertretend zuhören.
- Testen ohne Sprache: Edge mit `--user-data-dir` + `--load-extension` + `--remote-debugging-port`
  starten, `sidepanel.html?tab=<tabId>` als Popup öffnen (Testmodus im Code) und Befehle ins
  Eingabefeld tippen; per CDP steuerbar. Vorsicht: `msedge.exe --version` startet den Browser.
- `eval.py` prüft 55 Äußerungen + App-Auswahl gegen die echte Jev-API (mit `dryRun`, führt nichts
  am PC aus). Stand 2026-09-20: 55/55 und 6/6.
- Zusammenfassen/Fragen zur Seite laufen über LM Studio ([[lmstudio-tool]]), weil Jev keinen Text
  generiert.

**Geräte-Steuerung (seit 2026-09-23):** `gear.py` (SteelSeries Sonar + GG-Engine: Kanal-Lautstärke,
Stumm, Maus-DPI, Polling) und `hidbattery.py` (Akku der Aerox 5 per HID, ~25 % beim Test). Details
und Fallen in [[steelseries-local-api]]. CLI zum Testen: `python gear.py status|vol mikrofon 60|mute
mikrofon|dpi 800`. Sprachbefehle dafür sind verdrahtet (GEAR_ACTIONS/ANSWER_ACTIONS in intents.py, run_gear/run_answer in
server.py), dazu `answers.py` für Uhrzeit/Datum/Wetter (Open-Meteo)/Rechnen. eval.py: 66/66.
Offen: App-Steuerung für Claude/Discord (Nachricht diktieren mit Rückfrage vor dem Senden),
Timer (braucht Rückkanal zum Sprechen), lokale Erkennung per Whisper auf GPU 1 (RTX 3050,
`CUDA_VISIBLE_DEVICES=1`, GPU 0 ist die 5070).
