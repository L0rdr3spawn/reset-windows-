# Jev Voice Browser

Browser **und** Windows per Stimme steuern. Jev (TypeSafe System One) versteht die Äußerung und
liefert eine typisierte Entscheidung, der Code führt sie aus.

```
Mikrofon (Edge-Seitenleiste)  ->  server.py  ->  Jev  ->  Aktion
                                      |                    |
                                      |                    +-- Browser: Erweiterung (Tabs, Klicks, Vorlesen)
                                      +-- Windows: Tastatur/Fenster/Apps (desktop.py)
```

## Einrichten

1. **Server starten** – `start.cmd` doppelklicken (oder `python server.py`).
   Braucht `TYPESAFE_API_KEY` (Env, Registry oder `../cs2-jev/.env`) – wie `jev.py`.
2. **Erweiterung laden** – in Edge `edge://extensions` öffnen, *Entwicklermodus* an,
   *Entpackte Erweiterung laden* → Ordner `voice-browser/extension`.
3. **Mikrofon freigeben** – in der Seitenleiste *Einstellungen → Mikrofon-Zugriff einrichten*,
   dort einmal „Mikrofon erlauben“ klicken.
4. **Seitenleiste öffnen** – Jev-Symbol in der Leiste (oder `Alt+Shift+V`), dann auf das Mikrofon
   klicken bzw. `Alt+Shift+J`.

Die Spracherkennung ist die von Edge (braucht Internet). Brave und Chrome haben sie nicht –
deshalb ist Edge das „Ohr“. Edge darf im Hintergrund liegen; das Mikrofon läuft weiter, solange
die Seitenleiste offen ist.

## Diktattaste (wie Wispr Flow)

**Rechte Strg halten, sprechen, loslassen** – der geglättete Text erscheint dort, wo der Cursor
steht: Discord, Word, Editor, Suchfeld, Code, egal wo. Zweimal tippen = freihändig (nächster
Tastendruck beendet), Escape bricht ab, „streich das“ löscht das zuletzt Eingefügte.

**Overlay:** Beim Sprechen erscheint unten mittig eine schwebende Pille mit Pegelbalken und dem
laufenden Text, danach „Schreibe …“ und ein Haken. Sie nimmt nie den Fokus (WS_EX_NOACTIVATE),
der Text landet also im vorherigen Fenster. Abschalten: Häkchen *Schwebende Anzeige* oder
`"overlay": false`. Ohne Overlay läuft der Server ohne Fenster (`--no-overlay`).

**Taste ändern:** in der Seitenleiste unter *Einstellungen → Diktattaste* (wirkt sofort, ohne
Neustart) oder in `flow_config.json`. Erlaubt sind einzelne Tasten (`rctrl`, `ralt`, `rshift`,
`capslock`, `f9` … `f12`, `pause`, `scroll`, `rwin`) und Kombinationen wie `ctrl+space`,
`ctrl+alt+d`, `alt+y`. Bei Kombinationen hältst du alles zusammen; losgelassen wird über die
letzte Taste.

**Textaufbereitung, zweistufig:**

1. **Immer im Code:** Wörterbuch für Eigennamen (`jeff` → `Jev`), gesprochene Satzzeichen
   („Punkt“, „neue Zeile“), Füllwörter raus, Groß-/Kleinschreibung. Das reicht für sauberen Text
   und braucht kein Modell.
2. **Optional per lokalem LLM:** Selbstkorrekturen („nein, lieber …“), Grammatik, Umbrüche,
   Substantive groß. **Jev prüft das Ergebnis** („sagt es dasselbe wie das Diktat?“) – fällt es
   durch, wird Stufe 1 eingefügt. Danach zieht der Code nach, was er sicher weiß
   (`flow.polish`): Eigennamen aus dem Wörterbuch, Satzanfänge und jede Großschreibung, die in
   Stufe 1 schon stand. Das Modell ist bei Groß-/Kleinschreibung nicht zuverlässig, und was
   der Code sicher entscheiden kann, überlässt er ihm deshalb nicht. Höchstens `cleanup_wait` Sekunden (Standard 1,5) wird darauf gewartet; danach geht
   Stufe 1 raus, damit nichts hängt. Beim Tastendruck wird das Modell schon vorgewärmt.
   Abschalten: Häkchen *Text per lokalem LLM glätten* oder `"cleanup": false` – dann arbeitet Flow
   ganz ohne LM Studio.

Gemessen: ~1,8 s mit warmem Modell, ~2,6 s wenn es noch lädt, ~0,9 s ohne Glättung.
Ein kleines Modell (z. B. `gemma-4-e4b`) ist hier deutlich besser als ein 14B – der Server wählt
automatisch das kleinste passende, das in LM Studio geladen ist.

## Was geht

* **Browser (im Edge-Tab):** Seiten öffnen, suchen (Google, YouTube, Wikipedia, Amazon, Maps …),
  auf der Seite finden, klicken (per Name oder Nummer), in Felder tippen, Dropdowns, Checkboxen,
  scrollen, zu Abschnitten springen, Zoom, Dunkel- und Lesemodus, Tabs und Fenster, Videos
  (Pause, Spulen, Tempo, Lautstärke, Vollbild), Vorlesen, Zusammenfassen, Fragen zur Seite,
  Lesezeichen, Verlauf, Screenshot, Drucken, Kopieren/Einfügen, Diktat.
* **Windows (überall):** Programme starten und schließen, Fenster wechseln/minimieren/andocken,
  Systemlautstärke, Musiksteuerung (Spotify & Co.), beliebige Tastenkombinationen, Text ins aktive
  Programm tippen, Ordner und Einstellungsseiten öffnen, Windows-Suche, Task-Manager,
  Zwischenablage-Verlauf, Emoji-Auswahl, virtuelle Desktops, Helligkeit, Sperren, Herunterfahren.
* **In anderen Browsern (Brave, Chrome …):** Adresse öffnen, suchen, Tabs, Scrollen, Zoom, Suchen
  auf der Seite – alles über Tastenkürzel. Klicken per Elementname geht nur im Edge.

Die ganze Liste steht in der Seitenleiste unter **Befehle**, der Katalog in `intents.py`.

## Sicherheit

* Rückfrage vor: Kauf-/Senden-/Löschen-Klicks (Wortliste **und** Jev-Urteil), unsicherer
  Elementauswahl, „alle anderen Tabs schließen“, Fenster schließen, Herunterfahren/Neustart/Abmelden.
* Ja/Nein beantwortet Jev ebenfalls typisiert; „nein“ bricht ab.
* Herunterfahren läuft mit 30 s Vorlauf – „abbrechen“ stoppt es.
* Der API-Key bleibt im Server. Der Server hört nur auf `127.0.0.1` und nimmt nur Anfragen von
  Browser-Erweiterungen an.

## Aufbau

| Datei | Zweck |
| --- | --- |
| `server.py` | HTTP-Dienst: `/interpret`, `/execute`, `/pick`, `/llm`, `/type`, `/flow/*`, `/health` |
| `intents.py` | Aktionskatalog, Kandidaten, Zahlen, Schnellpfad, Policy (was Code entscheidet) |
| `desktop.py` | Windows: Tastatur (SendInput), Fenster, Apps, Ordner, Einstellungen, Helligkeit |
| `flow.py` | Diktattaste: globaler Tastatur-Hook, Zwischenablage, Textaufbereitung |
| `overlay.py` | Schwebende Anzeige beim Diktieren (Tkinter, ohne Fokusklau) |
| `eval.py` | 55 Beispieläußerungen + App-Auswahl gegen die echte Jev-API (`python eval.py`) |
| `test_text.py` | Textaufbereitung des Diktats, ohne API und ohne LM Studio (`python test_text.py`) |
| `extension/` | Seitenleiste (Mikrofon, Sprachausgabe, Ausführung), `content.js` für die Seite |
| `log.jsonl` | jede Äußerung mit erkannter Aktion – gut zum Nachschärfen |

### Wie Jev eingesetzt wird

Eine Anfrage pro Befehl mit mehreren unabhängigen Fragen parallel:

* `aktion` (Choice über ~140 Aktionen), `text` (Choice über alle Wortabschnitte der Äußerung –
  der Wert wird kopiert, nie erfunden), `ziel` (Suchmaschine/Seite), `element` (Choice über die
  Elemente der Seite), `fenster`, `tab`, `ordner`, `einstellung` und `heikel` (Noul: löst der
  Klick etwas Unumkehrbares aus?).
* Zweite Stufe nur beim App-Start: Choice über die installierten Programme (`Get-StartApps`).
* **Gegenprobe** vor folgenreichen Aktionen (Fenster schließen, PC sperren, freie
  Tastenkombination): eine zweite, unabhängige Noul-Frage, die nur noch die getroffene Wahl
  kennt – „wollte der Nutzer genau das?“. Unter 0,7 wird gefragt statt ausgeführt. Kostet ~0,6 s
  und läuft deshalb nur für das, was man nicht zurücknehmen kann (`server.FOLGENREICH`).
* Regeln bleiben im Code: Schwellen, Rückfragen, Zahlen, Richtung beim Spulen, Tastenkürzel.

Antwortzeit: ~0,7–1,0 s pro Befehl; eindeutige Kurzbefehle („runter“, „zurück“, „neuer Tab“)
laufen ohne Jev sofort.

## Zusammenfassen & Fragen zur Seite

Dafür wird das lokale LM Studio genutzt (`http://127.0.0.1:1234`, siehe `../lmstudio.py`),
weil Jev keine Texte generiert. Läuft LM Studio nicht, sagt die Seitenleiste das.

## Geräte & Antworten (ohne Browser)

`gear.py` steuert die SteelSeries-Hardware über die lokalen GG-APIs (Adressen kommen aus
`coreProps.json`, sie wechseln bei jedem GG-Start):

* Audio (Sonar): Lautstärke und Stumm für Gesamt, Spiel, Chat, Mikrofon, Medien, Aux.
* Maus (Engine): Sensi/DPI und Abfragerate lesen und setzen. Die DPI steht im Profil als
  Sensor-Byte, die Tabelle dazu liegt in `dpi_truemove_air.json` (TrueMove Air, mit Lücken).
* Akkustand: gibt die API nicht her, `hidbattery.py` fragt die Maus direkt per HID
  (Output-Report 0x92 bzw. 0xD2 im Funkbetrieb, Antwortbyte `((b & 0x7F) - 1) * 5` Prozent).

**Vor jeder Profiländerung** wird das alte Profil nach `backups/maus_<zeit>.json` gesichert:
ein leeres `PUT /configuration/<uuid>` leert ein Profil komplett (einmal passiert, aus der
Engine-Datenbank zurückgeholt).

`answers.py` beantwortet Uhrzeit, Datum, Wetter (Open-Meteo, kein Schlüssel) und Rechnen.
Der zuletzt genannte Ort wird in `answers_config.json` gemerkt, einmal „Wetter in <Stadt>“
sagen genügt. Umlaute werden beim Suchen ergänzt, sonst landet „Koeln“ irgendwo in Afrika.

Testen ohne Sprache:

    python gear.py status
    python answers.py wetter "morgen in Köln"
    python server.py --test "mach mein mikro stumm"        # Trockenlauf
    python server.py --test "wie viel akku hat meine maus" --echt
