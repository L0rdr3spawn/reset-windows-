# Jeff – Sprachassistent

**Starten:** Doppelklick auf `Jeff starten.cmd`. Das Skript beendet eine alte Instanz, macht den Selbsttest, startet Jeff im Hintergrund und wartet, bis er zuhört.
**Stoppen:** `Jeff stoppen.cmd`.
**Whisper auf die Grafikkarte:** `GPU einrichten.cmd`, einmalig (ca. 500 MB, nicht während eines Online-Spiels).

Jeff startet außerdem mit Windows (`python autostart.py status | ein | aus`).

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
- `letzter_befehl.wav` enthält, was Jeff zuletzt gehört hat.
- Befehle ohne Mikrofon testen: `python jev_assistent.py --befehl "wie spät ist es" --trocken --still`.
- Textlogik prüfen: `python tests.py`.

## Offen

- **Spotify-Zugang:** Ohne Client-ID öffnet „spiel …“ nur die Spotify-Suche. Für echtes Abspielen, Liken und Playlists eine App im Spotify-Developer-Dashboard anlegen, die Client-ID in `config.json` eintragen und `python jev_assistent.py --spotify-login` ausführen.
- **Discord-Stummschalten** braucht die Tastenkürzel `Strg+Umschalt+Alt+M` (Mikro) und `…+D` (taub) in den Discord-Einstellungen unter „Tastenbelegungen“.
