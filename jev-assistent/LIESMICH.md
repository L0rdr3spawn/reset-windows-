# Jeff – Sprachassistent

**Starten:** Doppelklick auf `Jeff starten.cmd`. Das Skript beendet eine alte Instanz, macht den Selbsttest, startet Jeff im Hintergrund und wartet, bis er zuhört.
**Stoppen:** `Jeff stoppen.cmd`.
**Whisper auf die Grafikkarte:** `GPU einrichten.cmd`, einmalig (ca. 500 MB, nicht während eines Online-Spiels).

**Autostart:** Jeff startet mit Windows über `Jeff.exe` (kleiner Starter, ruft unsichtbar `pythonw jev_assistent.py` auf und beendet sich gleich wieder; läuft Jeff schon, passiert nichts). Eingetragen ist er wie Discord oder Spotify unter `HKCU\…\CurrentVersion\Run` und erscheint dort mit seinem Namen („Jeff – Sprachassistent“, Herausgeber „Jev-Assistent“).
Ein- und ausschalten geht an jeder dieser Stellen:
- Windows-Einstellungen → Apps → Autostart
- Task-Manager → Autostart-Apps
- Jeffs Einstellungsfenster
- `python autostart.py status | ein | aus`

Wird Jeff in `config.json` umbenannt (`"name"`), aktualisiert `python autostart.py ein` (oder Aus/Ein im Einstellungsfenster) den Eintrag und den Namen in `Jeff.exe`. Die Quelle des Starters liegt in `launcher\` (`JeffLauncher.cs`, Symbol `jeff.ico`). `Jeff.exe` per Doppelklick startet Jeff ebenfalls, aber ohne Selbsttest.

## Einstellungen (Name, Weckwort, Tastenkürzel)

Doppelklick auf **„Jeff Einstellungen“** (Desktop oder dieser Ordner; startet `einstellungen.pyw` ohne Konsolenfenster):

- **Name des Assistenten** – z. B. „Kevin“. So nennt er sich in Ansagen, im Log und gegenüber Claude. Lautet das Weckwort noch „hey ‹alter Name›“, wandert es automatisch mit („hey kevin“).
- **Aktivierungswort (Weckwort)** – beliebig, aber die Weckwort-Erkennung (Vosk) kennt nur Wörter aus ihrem Wortschatz (≈ 223 000 deutsche Wörter, darunter viele Namen wie kevin, max, luna, jarvis). Ein unbekanntes Wort meldet das Fenster sofort rot – darauf würde er nie reagieren. Prüfen geht auch so: `python aktivierung.py "hey kevin"`.
- **Weckwort-Empfindlichkeit** – `weckwort_sicherheit` (0,40–0,90): niedriger reagiert leichter, höher gibt weniger Fehlalarme.
- **Tastenkürzel** – „Taste aufnehmen“, dann die Kombination drücken (z. B. Strg+Alt+J). Drückst du es irgendwo in Windows, piept er und hört sofort zu, ohne Weckwort. Einzelne Buchstaben ohne Strg/Alt/Win werden abgelehnt, belegte Kürzel auch. Steht in `config.json` als `"hotkey": "ctrl+alt+j"` (leer = aus).
- **Sprachausgabe** und **Mit Windows starten**.
- **Speichern & neu starten** – Änderungen gelten erst nach einem Neustart von Jeff; der Knopf erledigt das (Whisper lädt danach etwa 30 Sekunden, dann wird der Punkt grün).

Fehlt `"name"` oder `"hotkey"` in einer alten `config.json`, gilt „Jeff“ bzw. kein Tastenkürzel.

## Zum Ausprobieren

Sag vor jedem Befehl „hey jeff“, entweder in einem Satz oder mit kurzer Pause bis zum Piep.

| Sag | Erwartung |
|---|---|
| wie spät ist es | sagt die Uhrzeit („16 Uhr“ statt „16 Uhr 0“) |
| öffne youtube und such nach minecraft | **eine** YouTube-Suche (vorher öffnete sich nur YouTube) |
| starte spotify und dann spiel musik | Spotify startet, danach Play |
| stell einen timer auf zwei minuten → wie lange läuft der timer noch → timer abbrechen | Restzeit wird angesagt, Abbrechen klappt |
| nichts / vergiss es | Jeff bleibt still (vorher fragte er nach) |
| wer hat die glühbirne erfunden | Claude antwortet (ca. 4–5 s) |
| mach mal die mucke von dem apache typ an | Claude deutet es, Spotify-Suche öffnet sich |
| such in discord nach … | Discord kommt nach vorne, Suche läuft |
| im Spiel: drück escape | „Im Spiel drücke ich keine Tasten.“ |
| schreib in den editor hallo | tippt „hallo“, deine Zwischenablage (auch Bilder/Dateien) bleibt erhalten |

Im Spiel fluchen oder mit anderen reden: Löst Jeff aus Versehen aus, kommt nur ein tiefer Ton und keine Ansage mehr.

## Wenn etwas nicht klappt

- `python selbsttest.py` zeigt, was fehlt (Mikrofon, Jev, Claude, GPU, Spotify …).
- `jev-assistent.log` enthält nur echte Befehle. Tests und Trockenläufe stehen in `jev-test.log`.
- Reagiert Jeff zu selten auf „hey jeff“: Im Log stehen Zeilen wie `Weckwort verworfen (Sicherheit 0.58 unter 0.65)`. Dann `weckwort_sicherheit` in `config.json` etwas senken. Löst er zu oft aus, den Wert erhöhen.
- Reagiert er gar nicht auf ein neues Weckwort oder das Tastenkürzel: Beim Start steht im Log `Weckwort "…": "…" kennt die Weckwort-Erkennung nicht` bzw. `Tastenkürzel … nicht verfügbar (schon von einem anderen Programm belegt)`.
- `letzter_befehl.wav` enthält, was Jeff zuletzt gehört hat.
- Befehle ohne Mikrofon testen: `python jev_assistent.py --befehl "wie spät ist es" --trocken --still`.
- Textlogik prüfen: `python tests.py`.

## Offen

- **Spotify-Zugang:** Ohne Client-ID öffnet „spiel …“ nur die Spotify-Suche. Für echtes Abspielen, Liken und Playlists eine App im Spotify-Developer-Dashboard anlegen, die Client-ID in `config.json` eintragen und `python jev_assistent.py --spotify-login` ausführen.
- **Discord-Stummschalten** braucht die Tastenkürzel `Strg+Umschalt+Alt+M` (Mikro) und `…+D` (taub) in den Discord-Einstellungen unter „Tastenbelegungen“.
