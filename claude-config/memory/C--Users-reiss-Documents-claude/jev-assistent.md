---
name: jev-assistent
description: "Sprachassistent unter C:\\Users\\reiss\\jev-assistent (Weckwort \"hey jeff\") - Autostart, app-übergreifende Steuerung, Whisper auf GPU 1; nicht mit voice-browser verwechseln"
metadata:
  node_type: memory
  type: project
  originSessionId: 8b1f5fa3-0154-4d43-a98b-177017acb7f4
  modified: 2026-09-30T09:02:42.998Z
---

`C:\Users\reiss\jev-assistent\` — **das Hauptwerkzeug des Users**, nicht zu verwechseln mit
[[voice-browser]] (Browser-Seitenleiste). Weckwort „hey jeff" (Vosk hört mit, kleines Modell),
dann faster-whisper für den Satz, dann eine Jev-Anfrage mit allen Fragen parallel
(`ABSICHTEN`, App, Webseite, Spotify-Art, Discord-Ziel, seit 2026-09-23 auch Fenster + Mixer-Kanal).
Läuft als pythonw-Hintergrundprozess. **Seit 2026-09-26:** `Jeff starten.cmd` (stop → `selbsttest.py` →
start → `--status --warten`), `Jeff stoppen.cmd`, `GPU einrichten.cmd` (nvidia-cublas-cu12), `LIESMICH.md`
mit Testliste, `tests.py` (Textlogik offline). Einzelinstanz per Mutex `Local\JevAssistent` (jev.pid allein
war nach Herunterfahren veraltet → hätte fremden Prozess gekillt), Zustand in `jev.status`.
`--befehl/--wav/--trocken` loggen nach `jev-test.log`, echtes Log `jev-assistent.log`.
Weckwort braucht Vosk-`conf` ≥ `weckwort_sicherheit` (0.65; gemessen echt 1.00, "hey chef" 0.59).
Claude-„unklar“ = still (nur Ton), Abbruchwörter, Befehlsketten („öffne X und such Y“), Timer abbrechen/Rest,
Spielschutz auch für taste_druecken/text_schreiben, Zwischenablage sichert alle Formate + kein Win+V-Verlauf,
nach_vorne erst per AttachThreadInput (Alt-Tipp nur als Rückfall). Sicherung: `sicherung/2026-09-26_vor-durchsicht`.
Beim Starten aus Tools: `start ... <nul >nul 2>&1`, sonst hält pythonw die Ausgabe-Pipe fest.
**2026-09-26 abends:** cuBLAS installiert → Whisper wirklich auf GPU 1 (0,5 s). Live-Test 42/45; gefunden+behoben:
`prozess_laeuft` Dekodier-Absturz (OEM-„ü“), UWP-Apps (Rechner) nur per WM_CLOSE schließbar, „hier“ erzwingt
Programm-Suche, Chat-Apps (`"chat": true`) ohne Auto-Enter, Fokus-Prüfung direkt vor jedem Einfügen.
AttachThreadInput-Variante von nach_vorne wieder raus (Wirkung auf Tastaturfokus unbewiesen) → Alt-Tipp bleibt.
**Live-Tests mit echten Tasten NIE, während der User am PC ist:** er tippte parallel in Discord, meine
Testtexte landeten in seinem Nachrichtenentwurf. Vorher Leerlauf prüfen (GetLastInputInfo) oder nur Trockenlauf.
Brave = Standardbrowser, jetzt in config apps.
**2026-09-30 „startet nicht automatisch“:** Ursache war NICHT der Code, sondern Windows-Autostart-Apps:
`HKCU\...\Explorer\StartupApproved\StartupFolder` → `Jev-Assistent.lnk` = 03… (aus), gesetzt 29.09 21:56,
4 min nach der Wallpaper-Engine-Aufräumaktion. Die .lnk bleibt dabei liegen und wird still ignoriert.
`autostart.py status/ein` und `selbsttest.py` erkennen/beheben das jetzt (02… = an). Der PC nutzt Standby
und Ruhezustand, echte Anmeldungen gibt es trotzdem regelmäßig; Jeff überlebt Standby (10:40 am 29.09).

**Stand 2026-09-23 (was ich ergänzt habe):**
- `autostart.py ein|aus|status` — Verknüpfung im Autostart-Ordner auf pythonw (vorher startete nichts von allein).
- `fenster.py` — offene Fenster auflisten/suchen/nach vorne holen; damit wirkt der Assistent in **jedem**
  Programm: neue Absichten `app_wechseln`, `text_schreiben` (auch „schreib in claude …"), `taste_druecken`.
- Geräte + Antworten über die getesteten Module aus voice-browser (per `sys.path`): `geraet_status`
  (Maus-Akku/Sensi), `kanal_lautstaerke`, `kanal_stumm`, `maus_sensi`, `wetter`, `rechnen`.
- Whisper läuft jetzt auf **GPU 1 = RTX 3050** (`whisper_gpu` in config.json, float16, Rückfall auf CPU),
  damit die 5070 frei bleibt.

**Teuer gelernte Details:**
- **SendInput braucht Scancodes** (`MapVirtualKeyW(vk, 0)`): ohne sie ignorieren WinUI-Programme wie
  Notepad 11 die Tastenkürzel (Strg+S/Strg+V kamen nicht an) und einzeln getippte Unicode-Zeichen
  gehen verloren oder werden verfälscht („eins zwei" → „nnns iiii"). Text deshalb per
  `tastatur.einfuegen()` (Zwischenablage + Strg+V, alte Zwischenablage wird zurückgelegt).
- `laufende_pid()` dekodierte die `tasklist`-Ausgabe ohne `errors="replace"` → UnicodeDecodeError,
  der Assistent startete gar nicht. Bei allen `subprocess.run(..., text=True)` unter Windows daran denken.
- Ein ausdrücklich genanntes Ziel („in den editor") muss Jevs Fensterwahl **schlagen**, sonst landet
  der Text im gerade aktiven Fenster (ist mir passiert: Text ging an Discord statt in den Editor).
- Gesprochene Programmnamen über `config.json` auf Prozessnamen abbilden: „Editor" steht in Windows 11
  nirgends im Fenstertitel, das Fenster heißt „… – Notepad".
- Notepad 11 merkt sich **ungespeicherte Tabs** unter
  `%LOCALAPPDATA%\Packages\Microsoft.WindowsNotepad_8wekyb3d8bbwe\LocalState\TabState`. Beim Testen dort
  hineinschreiben heißt: fremde Dateien können unbemerkt geänderte Tab-Stände bekommen. Zum Testen eine
  eigene Datei in %TEMP% öffnen, hinterher Tab-Stände prüfen.
- **2026-09-25: GPU-Whisper lief nie wirklich** — Modell lädt auf cuda, aber `cublas64_12.dll` fehlt
  (nur ctranslate2 bringt cudnn mit), Absturz erst beim ersten Transkribieren → jeder Befehl scheiterte.
  `_whisper_laden` macht jetzt einen Probelauf und fällt auf CPU zurück (int8, `cpu_threads=4`, ~1,3 s).
  Für echte GPU: `pip install nvidia-cublas-cu12` + DLL-Ordner per `os.add_dll_directory` — noch offen,
  User spielte gerade (Download/Neustart nicht während des Spielens).
- Dabei gefunden: `self.benachrichtigungen.start()` war hinter das `return` in `_whisper_laden` gerutscht
  (Discord-Neuigkeiten liefen nie) — zurück in `__init__` verschoben.
- **2026-09-25: Absicht `suchen`** + Jev-Frage `such_ort` (youtube/google/spotify/twitch/netflix/amazon/
  wikipedia/pc_dateien/programm). Begriff per Regex `suchbegriff()`, Such-URLs als `"suche"` in
  config.json-webseiten; Spotify über `spotify:search:` (kein API-Zugang, client_id leer), PC über
  `search-ms:`, Programme per `suche_taste` (Standard Strg+F) + Einfügen + Enter.
  `ist_spiel()` (Pfad mit `\steamapps\` oder `spiele` in config.json) sperrt Tastendrücke ins Spiel —
  User spielt oft CS2 nebenher, aktives Fenster war beim Testen cs2.exe. Echte Klick-Tests nur, wenn er nicht spielt.
- **2026-09-25: Claude als Sprachverständnis** (`claude.py`): bei `sonstiges`/niedriger Sicherheit und
  neuer Absicht `claude_fragen` ruft Jeff `claude -p --model sonnet` (Abo, kein API-Key; `--bare` geht
  deshalb nicht) mit `--tools "" --setting-sources "" --strict-mcp-config --no-session-persistence`,
  `MAX_THINKING_TOKENS=0` (sonst ~10 s statt ~4,5 s), cwd `claude-leer/`, `CREATE_NO_WINDOW` (kein
  Fokusklau im Spiel). Antwort-JSON: befehl → nochmal durch Jev (`von_claude=True`, keine Schleife),
  antwort → vorlesen. Ein-/aus + Modell in config.json `claude`.
- Spotify-API nicht eingerichtet (client_id leer): `spotify_abspielen` öffnet ersatzweise die Spotify-Suche.
- In `C:\Users\reiss\Downloads\jev.txt` liegt sein TypeSafe-API-Key im Klartext — Datei nicht anzeigen.
