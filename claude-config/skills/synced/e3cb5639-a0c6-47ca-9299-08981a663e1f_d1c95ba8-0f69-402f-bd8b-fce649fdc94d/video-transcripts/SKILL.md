---
name: video-transcripts
description: Holt das Transkript (Untertitel) eines Videos von YouTube, TikTok oder Instagram und liefert es als saubere Markdown-Datei. Diesen Skill IMMER verwenden, wenn der Nutzer einen Video-Link schickt und ein Transkript, Untertitel, Subtitles, den gesprochenen Text, eine Mitschrift oder eine Zusammenfassung des Gesagten will – auch bei Formulierungen wie "was wird in dem Video gesagt?", "transkribier das", "hol mir den Text aus dem Video" oder wenn nur eine Video-URL ohne weitere Erklärung geschickt wird und Transkription naheliegt.
---

# Video-Transkripte (YouTube / TikTok / Instagram)

Dieser Skill liest **vorhandene Untertitel** (manuell oder automatisch erzeugt) eines Videos aus und speichert sie als Markdown-Datei. Es wird kein Audio transkribiert.

## Weg 1: Skript (bevorzugt – braucht Netzzugang zur Videoplattform)

Funktioniert in Claude Code auf dem Rechner des Nutzers oder in jeder Umgebung, in der `youtube.com`/`tiktok.com`/`instagram.com` per Netz erreichbar sind.

1. Falls nötig: `pip install yt-dlp --break-system-packages`
2. Ausführen:
   ```
   python scripts/get_transcript.py "<VIDEO_URL>" --lang de --outdir <ZIELORDNER>
   ```
   Optionen: `--lang <code>` bevorzugte Sprache (Fallback-Reihenfolge: gewünschte Sprache → de → en → erste verfügbare), `--timestamps` für `[MM:SS]`-Marken pro Absatz.

   **Instagram (und private/login-pflichtige Videos):** Instagram stellt keine Untertitel-Spuren bereit und verlangt Login. Der funktionierende Weg ist daher: Tonspur laden und lokal per Whisper transkribieren, mit Login-Cookies aus dem Browser des Nutzers:
   ```
   pip install faster-whisper
   python scripts/get_transcript.py "<REEL_URL>" --audio-fallback --cookies-from-browser chrome --lang de --outdir <ZIELORDNER>
   ```
   (`chrome` durch den Browser des Nutzers ersetzen: `firefox`, `edge`, `safari`, `brave` …; alternativ `--cookies <pfad/zu/cookies.txt>`. Vorher fragen bzw. ankündigen, dass die Browser-Cookies des Nutzers für den Login verwendet werden.) `--audio-fallback` hilft genauso bei TikTok-/YouTube-Videos ohne Untertitel. Die Whisper-Transkription läuft komplett lokal; beim ersten Lauf wird das Sprachmodell heruntergeladen, längere Videos brauchen entsprechend Zeit.
3. Das Skript gibt bei Erfolg den Pfad der fertigen Markdown-Datei aus (Titel, Kanal, URL, Sprache, Transkript in Absätzen). Datei dem Nutzer übergeben (in Claude.ai: nach `/mnt/user-data/outputs/` legen und mit `present_files` zeigen) und in 1–2 Sätzen sagen, worum es im Video geht.

**Exit-Codes:** `2` = Video hat keine Untertitel → dem Nutzer genau das sagen. `3` = Netzwerk/Zugriff blockiert (z. B. Claude.ai-Sandbox, Login-Wand, privates Video) → zu Weg 2 wechseln und dem Nutzer den Grund nennen.

**Plattform-Hinweise:** YouTube funktioniert fast immer (auch Auto-Untertitel). TikTok: erst normal versuchen, bei Exit 2 mit `--audio-fallback` wiederholen. Instagram: direkt den Audio-Fallback mit Cookies verwenden (siehe oben).

## Weg 2: Web-Recherche (Fallback ohne Plattform-Zugang, z. B. Claude.ai)

Hier gilt: Im Chat darf **kein komplettes Transkript wortwörtlich reproduziert** werden (Urheberrecht). Stattdessen:

1. Video-URL mit `web_fetch` abrufen – auch bei Bot-Schutz liefert der Fetcher meist **Titel, Kanal und Beschreibung** aus den Metadaten.
2. Per `web_search` nach `<Videotitel> transcript` (bzw. `Transkript`) suchen. Für bekannte Videos (TED, Podcasts, populäre Kanäle) gibt es oft Seiten mit dem vollständigen Transkript; bei TED-Talks immer `ted.com` mit `?view=transcript` bevorzugen.
3. Dem Nutzer den **Link zur Transkript-Seite** geben und auf Basis der Quelle eine **eigenständige Zusammenfassung / Kernaussagen in eigenen Worten** liefern (mit maximal einem kurzen Zitat unter 15 Wörtern). Fragen zum Inhalt beantworten ist okay – das vollständige Transkript abtippen nicht.
4. Wenn der Nutzer die Volltext-Datei will: erklären, dass das über Claude Code mit diesem Skill direkt geht (Weg 1), oder dass er den Text auf der verlinkten Seite selbst kopieren kann.

## Mehrere Links

Pro Video eine Datei bzw. ein Abschnitt. Fehler pro Video einzeln berichten, nicht den ganzen Auftrag abbrechen.

## Grenzen (transparent kommunizieren)

- Whisper-Transkription enthält (wie Auto-Untertitel) Erkennungsfehler.
- Private oder regional gesperrte Videos brauchen Login-Cookies; ohne gültigen Login geht es nicht.
- In Claude.ai (Sandbox ohne Plattform-Zugang) funktioniert nur Weg 2 – Instagram dort gar nicht, das ehrlich sagen und auf Claude Code verweisen.
