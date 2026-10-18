#!/usr/bin/env python3
"""
Holt Untertitel/Transkripte von YouTube, TikTok oder Instagram per yt-dlp
und speichert sie als saubere Markdown-Datei.

Benoetigt: pip install yt-dlp   (und Netzwerkzugang zur jeweiligen Plattform)

Verwendung:
    python get_transcript.py <VIDEO_URL> [--lang de] [--timestamps] [--outdir PFAD]

Exit-Codes:
    0 = Erfolg
    2 = Keine Untertitel vorhanden
    3 = Netzwerk-/Zugriffsfehler (z. B. Sandbox ohne Zugang zur Plattform, Login-Wand)
"""

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def pick_track(subs, wanted):
    """Waehle den besten Untertitel-Track: gewuenschte Sprache > de > en > erster."""
    if not subs:
        return None
    for lang in [wanted, wanted.split("-")[0], "de", "en"]:
        if not lang:
            continue
        for key in subs:
            if key == lang or key.startswith(lang + "-") or key.startswith(lang + "_"):
                return key
    return sorted(subs.keys())[0]


def vtt_to_segments(vtt_text):
    """Parst WebVTT zu [(startzeit_sekunden, text), ...] und entfernt Duplikate."""
    segments = []
    time_re = re.compile(r"(\d+):(\d+):(\d+)[.,](\d+)\s*-->")
    short_re = re.compile(r"(\d+):(\d+)[.,](\d+)\s*-->")
    current_start = None
    buf = []
    last_text = ""

    def flush():
        nonlocal buf, current_start, last_text
        if current_start is not None and buf:
            text = " ".join(buf).strip()
            text = re.sub(r"<[^>]+>", "", text)          # Inline-Tags (<c>, <00:00:01.000>)
            text = html.unescape(text)
            text = re.sub(r"\s+", " ", text).strip()
            if text and text != last_text:
                segments.append((current_start, text))
                last_text = text
        buf = []
        current_start = None

    for line in vtt_text.splitlines():
        line = line.strip("\ufeff").rstrip()
        m = time_re.match(line)
        s = short_re.match(line) if not m else None
        if m:
            flush()
            h, mi, se, _ = m.groups()
            current_start = int(h) * 3600 + int(mi) * 60 + int(se)
        elif s:
            flush()
            mi, se, _ = s.groups()
            current_start = int(mi) * 60 + int(se)
        elif line and not line.startswith(("WEBVTT", "NOTE", "Kind:", "Language:", "STYLE")) \
                and not re.fullmatch(r"\d+", line) and not line.startswith("align:"):
            if current_start is not None:
                buf.append(line)
    flush()

    # Rollende Duplikate entfernen (typisch bei Auto-Untertiteln)
    cleaned = []
    for t, text in segments:
        if cleaned and (text in cleaned[-1][1] or cleaned[-1][1] in text):
            if len(text) > len(cleaned[-1][1]):
                cleaned[-1] = (cleaned[-1][0], text)
            continue
        cleaned.append((t, text))
    return cleaned


def fmt_ts(sec):
    return f"[{sec // 60:02d}:{sec % 60:02d}]"


def transcribe_audio(url, extra, lang):
    """Laedt die Tonspur und transkribiert lokal mit faster-whisper.
    Rueckgabe: (segments, sprach_label) oder ([], None) bei Fehler."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("WHISPER FEHLT: bitte zuerst `pip install faster-whisper` ausführen "
              "(und ggf. ffmpeg installieren).", file=sys.stderr)
        return [], None

    with tempfile.TemporaryDirectory() as tmp:
        dl = run(["yt-dlp", "-f", "bestaudio/best", "-o", f"{tmp}/audio.%(ext)s",
                  "--no-playlist", *extra, url])
        files = [f for f in Path(tmp).glob("audio.*")]
        if dl.returncode != 0 or not files:
            err = dl.stderr.strip().splitlines()[-1] if dl.stderr.strip() else "?"
            print(f"ZUGRIFFSFEHLER beim Audio-Download: {err}", file=sys.stderr)
            print("Tipp: Bei Instagram/privaten Videos --cookies-from-browser chrome "
                  "(oder firefox/edge) mitgeben.", file=sys.stderr)
            return [], None

        print("Transkribiere Tonspur lokal mit Whisper (Modell 'small') ...", file=sys.stderr)
        model = WhisperModel("small", compute_type="int8")
        whisper_lang = lang.split("-")[0] if lang else None
        segs, info = model.transcribe(str(files[0]), language=whisper_lang, vad_filter=True)
        out = [(int(s.start), s.text.strip()) for s in segs if s.text.strip()]
        detected = getattr(info, "language", whisper_lang or "?")
        return out, f"{detected} (per Whisper-Spracherkennung transkribiert, keine Untertitel vorhanden)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--lang", default="de", help="Bevorzugte Sprache (Standard: de)")
    ap.add_argument("--timestamps", action="store_true", help="Zeitstempel pro Absatz behalten")
    ap.add_argument("--outdir", default=".", help="Zielordner")
    ap.add_argument("--cookies-from-browser", default=None,
                    help="Browser für Login-Cookies, z. B. chrome, firefox, edge (für Instagram/private Videos)")
    ap.add_argument("--cookies", default=None, help="Pfad zu einer cookies.txt-Datei")
    ap.add_argument("--audio-fallback", action="store_true",
                    help="Wenn keine Untertitel existieren: Tonspur laden und lokal per Whisper transkribieren (braucht: pip install faster-whisper)")
    args = ap.parse_args()

    extra = []
    if args.cookies_from_browser:
        extra += ["--cookies-from-browser", args.cookies_from_browser]
    if args.cookies:
        extra += ["--cookies", args.cookies]

    # 1. Metadaten + verfuegbare Untertitel abfragen
    probe = run(["yt-dlp", "-J", "--skip-download", *extra, args.url])
    if probe.returncode != 0:
        err = probe.stderr.strip().splitlines()[-1] if probe.stderr.strip() else "Unbekannter Fehler"
        if any(k in probe.stderr.lower() for k in ["login", "rate-limit", "private", "cookies", "unable to download", "network", "resolve", "timed out", "403", "blocked", "certificate", "ssl"]):
            print(f"ZUGRIFFSFEHLER: {err}", file=sys.stderr)
            sys.exit(3)
        print(f"FEHLER: {err}", file=sys.stderr)
        sys.exit(3)

    info = json.loads(probe.stdout)
    if info.get("_type") == "playlist" and info.get("entries"):
        info = info["entries"][0]

    title = info.get("title") or "video"
    uploader = info.get("uploader") or info.get("channel") or info.get("uploader_id") or "unbekannt"
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    track_key, auto_used = None, False
    source = manual
    track_key = pick_track(manual, args.lang)
    if not track_key:
        track_key = pick_track(auto, args.lang)
        source, auto_used = auto, True

    segments = []
    lang_label = None

    if not track_key:
        if not args.audio_fallback:
            print("KEINE UNTERTITEL: Dieses Video hat keine (öffentlichen) Untertitel. "
                  "Tipp: mit --audio-fallback die Tonspur lokal per Whisper transkribieren.", file=sys.stderr)
            sys.exit(2)
        segments, lang_label = transcribe_audio(args.url, extra, args.lang)
        if not segments:
            sys.exit(2)
    else:
        # 2. Untertitel-Datei laden
        with tempfile.TemporaryDirectory() as tmp:
            sub_flag = "--write-auto-subs" if auto_used else "--write-subs"
            dl = run(["yt-dlp", "--skip-download", sub_flag, "--sub-langs", track_key,
                      "--sub-format", "vtt/srt/best", "-o", f"{tmp}/sub.%(ext)s", *extra, args.url])
            files = list(Path(tmp).glob("sub.*"))
            if dl.returncode != 0 or not files:
                print(f"FEHLER beim Untertitel-Download: {dl.stderr.strip().splitlines()[-1] if dl.stderr.strip() else '?'}", file=sys.stderr)
                sys.exit(3)
            raw = files[0].read_text(encoding="utf-8", errors="replace")
        segments = vtt_to_segments(raw)
        lang_label = f"{track_key}" + (" (automatisch erzeugt)" if auto_used else " (manuelle Untertitel)")

    if not segments:
        print("KEINE UNTERTITEL: Untertitel-Datei war leer.", file=sys.stderr)
        sys.exit(2)

    # 3. Markdown schreiben (Absatz je ~60 s)
    lines = [f"# {title}", "",
             f"- Kanal/Account: {uploader}",
             f"- URL: {info.get('webpage_url', args.url)}",
             f"- Sprache: {lang_label}",
             "", "## Transkript", ""]
    para, para_start = [], segments[0][0]
    for t, text in segments:
        if para and t - para_start >= 60:
            prefix = fmt_ts(para_start) + " " if args.timestamps else ""
            lines.append(prefix + " ".join(para))
            lines.append("")
            para, para_start = [], t
        para.append(text)
    if para:
        prefix = fmt_ts(para_start) + " " if args.timestamps else ""
        lines.append(prefix + " ".join(para))

    safe = re.sub(r"[^\w\s-]", "", title).strip().lower()
    safe = re.sub(r"[\s_-]+", "-", safe)[:60] or "video"
    out = Path(args.outdir) / f"transkript-{safe}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
