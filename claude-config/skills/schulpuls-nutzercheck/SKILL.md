---
name: schulpuls-nutzercheck
description: Zweiter Check / User-Check / Nutzer-Check / Beta-Test fuer Schulpuls (Schulmanager) - kritische Pruefung eines Bereichs auf Benutzerfreundlichkeit, Aussehen, Verstaendlichkeit, Modularitaet und Barrierefreiheit durch die lokalen OpenClaw-Agenten (sm-admin, sm-tester-a, sm-tester-b) plus eigene Gegenpruefung durch Claude. Verwenden, wenn der User einen "zweiten Check", "User-Check", "Nutzer-Check", "Betatest", "kritisch drueber gucken", "wie benutzerfreundlich/modular ist das" fuer eine Seite oder einen Bereich will, oder nachdem Claude in Schulpuls ein Feature fertig gebaut hat und es pruefen lassen soll. Immer zusammen mit dem Skill schulpuls-atlas.
---

# Schulpuls-Nutzercheck

Lokaler Beta-Test mit drei OpenClaw-Agenten (Gemma auf der RTX 5070) und anschliessender kritischer Gegenpruefung durch Claude.

## Bestandteile

- Ordner (Ergebnisse fuer den User): `C:\Users\reiss\Documents\Schulpuls-Betatest\` mit `patches\`, `berichte\`, `status.json`, `verlauf.log`, `LIESMICH.md`.
- Ablauf: `...\Schulpuls-Betatest\skripte\betatest-runde.ps1` (`-Bereich <slug>`, `-Alle`, `-Neu`, `-OhneKopie`). Pro Bereich: Server-Kopie holen, Admin teilt in Auftrag A (Demo: Bedienung/Aussehen) und B (Code), beide Tester gleichzeitig, Gegenpruefung ueber Kreuz, Admin schreibt Update-Patch.
- Server-Kopie (nur Code, ohne DB/.env/Lizenzserver/Tests): `~\.openclaw\workspace-sm-admin\schulmanager-kopie\` (`skripte\kopie-holen.ps1`).
- Demo zum Klicken: https://schulmanager-demo.l0rdr3spawn.duckdns.org:10489 . Demo-Zugaenge traegt NUR der User ein (`Desktop\Betatest Zugaenge eintragen.cmd` -> `~\.openclaw\secrets\betatest-zugaenge.json`). Claude liest diese Datei nie und gibt nie selbst Passwoerter ein.
- Bereichs-Slugs = Bereichsdateien des Atlas (`features/<slug>.md`, Liste in `INDEX.md`).

## Ablauf

1. **Bereich bestimmen**: mit `atlas.py find <begriff>` bzw. `INDEX.md` den Slug finden (z. B. `nachrichten`, `klassenbuch`, `stundenplan`).
2. **OpenClaw muss laufen** (Port 18789). Pruefen: `Get-NetTCPConnection -LocalPort 18789 -State Listen`. Wenn nicht: den User bitten, `Desktop\OpenClaw starten` zu klicken, oder `Programme\openclaw-runner\openclaw-start.ps1` ueber eine einmalige Aufgabenplaner-Aufgabe starten (Claude-App ist MSIX: OpenClaw-CLI direkt aus Claude scheitert an "offline maintenance"). Belegt die RTX 5070 (vorher fragen, wenn CS2 laeuft).
3. **Runde starten - immer ueber den Aufgabenplaner**, nie direkt aus Claude:
   ```powershell
   $S = "C:\Users\reiss\Documents\Schulpuls-Betatest\skripte\betatest-runde.ps1"
   $id = [guid]::NewGuid().ToString("N").Substring(0,6); $log = "$env:TEMP\bt-$id.log"; $done = "$log.done"   # Log-Name jedes Mal neu!
   Register-ScheduledTask -TaskName "Betatest-$id" -Action (New-ScheduledTaskAction -Execute powershell.exe -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"& '$S' -Bereich <slug> *> '$log'; 'x' | Out-File '$done'`"") -Principal (New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive) | Out-Null
   Start-ScheduledTask -TaskName "Betatest-$id"
   # warten bis $done existiert (im Hintergrund; eine Runde dauert ca. 5-20 min), dann Unregister-ScheduledTask
   ```
4. **Ergebnis lesen**: neuester Patch in `patches\` und die vier Dateien in `berichte\` mit gleichem Zeitstempel.
5. **Eigene Gegenpruefung (Pflicht)** - Gemma E4B ist klein und irrt sich oft:
   - Jeden Befund am Code pruefen (Atlas -> nur genannte Abschnitte lesen): bestaetigt / falsch / unklar.
   - Diffs nie ungeprueft uebernehmen; Pfade beziehen sich auf die Kopie, das Repo ist `C:\Users\reiss\Documents\claude\Claude.Code-merge`.
   - Selbst kritisch ergaenzen, Pruefliste:
     - Bedienbarkeit: Klickzahl fuer Haeufiges, Rueckmeldung nach Aktionen, Fehlermeldungen verstaendlich, Leerzustaende, Rueckgaengig/Bestaetigung bei Gefaehrlichem.
     - Aussehen/Konsistenz: Design-Tokens statt fester Farben, gleiche Muster wie andere Seiten, ein Raster (`DayPeriodGrid`), dunkles Schema.
     - Verstaendlichkeit: Sie-Form ueberall, Fachbegriffe, Hilfe ueber HelpTip statt Erklaertexten, keine Emojis.
     - Modularitaet: Dateigroesse, Doppelungen, klare Grenzen zwischen Bereichen, wiederverwendete Komponenten, Rechtepruefung im Backend.
     - Barrierefreiheit: Tastatur, Fokus, Beschriftungen fuer Screenreader, Kontrast, Handy-Breite.
6. **Bericht an den User**: kurz, nach Prioritaet; sagen, welche Agenten-Befunde stimmen und welche nicht. Nichts automatisch umsetzen - erst fragen, ob Claude die bestaetigten Punkte im Repo umsetzen soll (dann normale Schulpuls-Regeln: Atlas, nur Tests der geaenderten Bereiche, nicht committen ohne Auftrag).
7. Danach anbieten, `Desktop\OpenClaw stoppen` auszufuehren (gibt RTX 5070 frei, startet Handy neu).

## Nur-Claude-Variante

Wenn OpenClaw nicht laufen soll oder es schnell gehen muss: Claude macht den Check allein mit derselben Pruefliste, am Code (Atlas) und - fuer oeffentliche Seiten - im eingebauten Browser auf der Demo. Anmeldung in der Demo uebernimmt der User selbst; Claude gibt keine Passwoerter ein.

## Fallstricke

- Log-Datei pro Lauf neu benennen: ein Lauf, der Handy neu startet, vererbt den Datei-Handle -> spaetere Laeufe mit derselben Datei starten nie.
- `status.json`: Bereiche mit `fehler` werden beim naechsten Lauf ohne `-Bereich` erneut versucht.
- Agenten haben keine Schreib-/Ausfuehr-Werkzeuge (tools.deny); Dateien schreibt nur das Ablauf-Skript.
- Niemals die Hauptinstanz oder echte Konten fuer Tests verwenden; Betatester-Konten auf der Hauptinstanz erst nach Deploy des Beobachtungs-Features (Atlas doku/intern/WEITER-MORGEN.md).
