"""Jev-Assistent: wartet im Hintergrund auf "hey jev" und führt PC-Befehle aus.

Das Weckwort erkennt Vosk offline. Den Befehl danach schreibt Whisper (ebenfalls
lokal) auf, Jev entscheidet, was gemeint ist, und dieser Code führt es aus.

  python jev_assistent.py                  Mikrofon, läuft dauerhaft
  python jev_assistent.py --befehl "..."   einen Befehl direkt testen
  python jev_assistent.py --wav datei.wav  Audiodatei statt Mikrofon
  python jev_assistent.py --trocken ...    nur anzeigen, nichts ausführen
  python jev_assistent.py --spotify-login  einmalig bei Spotify anmelden
  python jev_assistent.py --stop           laufende Instanz beenden
"""

import argparse
import ctypes
import datetime
import json
import logging
import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import wave
import webbrowser
import winreg
import winsound
from logging.handlers import RotatingFileHandler
from pathlib import Path

import numpy as np

import claude
import discord_steuerung
import fenster
import spotify_steuerung
import tastatur

# Geraete- und Antwort-Module liegen beim Voice-Browser-Projekt und sind dort getestet;
# fehlen sie, laufen nur die davon abhaengigen Befehle nicht.
sys.path.append(r"C:\Users\reiss\Documents\claude\voice-browser")
try:
    import gear      # SteelSeries: Sonar-Kanaele, Maus-DPI, Akku
    import answers   # Wetter, Rechnen
except Exception:    # noqa: BLE001 - egal warum, dann eben ohne
    gear = answers = None

BASIS = Path(__file__).resolve().parent
CONFIG = json.loads((BASIS / "config.json").read_text(encoding="utf-8"))
MODELL = BASIS / "vosk-model-small-de-0.15"
PID_DATEI = BASIS / "jev.pid"
SPOTIFY_TOKEN = BASIS / ".spotify-token"

log = logging.getLogger("jev")

# Absicht -> Taste für Lautstärke und Medien
MEDIENTASTEN = {
    "lauter": "lauter",
    "leiser": "leiser",
    "stumm": "stumm",
    "musik_pause": "play_pause",
    "naechstes_lied": "naechstes",
    "vorheriges_lied": "vorheriges",
}

ABSICHTEN = {
    "app_oeffnen": {"what": "Ein Programm auf dem PC starten oder öffnen", "examples": ["öffne spotify", "starte discord", "mach den rechner auf"]},
    "app_schliessen": {"what": "Ein laufendes Programm beenden oder schließen", "examples": ["schließe spotify", "beende discord"]},
    "webseite_oeffnen": {"what": "Eine Webseite im Browser aufrufen", "not_for": "Auf einer Seite nach etwas Bestimmtem suchen", "examples": ["öffne youtube", "geh auf google", "zeig mir das wetter"]},
    "lauter": {"what": "Die Lautstärke des PCs erhöhen", "examples": ["mach lauter", "lauter bitte"]},
    "leiser": {"what": "Die Lautstärke des PCs verringern", "examples": ["mach leiser", "leiser"]},
    "stumm": {"what": "Den Ton des PCs ganz aus- oder wieder einschalten", "not_for": "Das Mikrofon oder den Ton in Discord", "examples": ["ton aus", "pc stumm", "ton wieder an"]},
    "musik_pause": {"what": "Musik starten, pausieren oder fortsetzen, ohne einen bestimmten Song, Künstler oder eine Playlist zu nennen", "examples": ["pause", "musik stopp", "spiel weiter", "starte musik auf spotify", "mach musik an"]},
    "naechstes_lied": {"what": "Zum nächsten Lied springen", "examples": ["nächstes lied", "überspringen", "skip"]},
    "vorheriges_lied": {"what": "Zum vorherigen Lied zurück", "examples": ["vorheriges lied", "lied zurück"]},
    "spotify_abspielen": {"what": "Bestimmte Musik auf Spotify abspielen: einen Song, Künstler, ein Album oder eine Playlist", "not_for": "Pausierte Musik einfach fortsetzen, oder in Spotify nur suchen statt abspielen", "examples": ["spiel was von apache 207", "spiel meine gym playlist", "spiel bohemian rhapsody"]},
    "spotify_liken": {"what": "Den gerade laufenden Song liken oder zu den Lieblingssongs hinzufügen", "examples": ["like den song", "speicher das lied", "gefällt mir"]},
    "spotify_shuffle": {"what": "Die Zufallswiedergabe (Shuffle) ein- oder ausschalten", "examples": ["shuffle an", "zufallswiedergabe aus"]},
    "spotify_was_laeuft": {"what": "Fragen, welcher Song gerade läuft", "examples": ["was läuft gerade", "wie heißt der song"]},
    "discord_mikro": {"what": "In Discord das eigene Mikrofon stumm- oder wieder anschalten", "examples": ["mikro aus", "mute mich", "mikro wieder an"]},
    "discord_taub": {"what": "In Discord taub schalten (deafen), also den Discord-Ton und das Mikro aus- oder anschalten", "examples": ["discord ton aus", "deafen", "taub schalten"]},
    "discord_oeffnen": {"what": "In Discord einen Server, Kanal oder den Chat mit einer Person öffnen oder einem Sprachkanal beitreten", "examples": ["öffne den gaming kanal", "geh in den chat mit max", "tritt dem sprachkanal zocken bei"]},
    "discord_nachricht": {"what": "Eine Nachricht an eine Person oder in einen Kanal auf Discord schreiben", "examples": ["schreib max bin gleich da", "schreib in general wer ist online"]},
    "discord_neuigkeiten": {"what": "Neue Discord-Nachrichten oder -Benachrichtigungen vorlesen lassen", "examples": ["was gibt's neues auf discord", "lies meine nachrichten vor", "hab ich nachrichten"]},
    "timer": {"what": "Einen Timer oder Wecker für eine Dauer stellen", "examples": ["stell einen timer auf fünf minuten", "timer zehn minuten"]},
    "uhrzeit": {"what": "Nach der aktuellen Uhrzeit fragen", "examples": ["wie spät ist es", "uhrzeit"]},
    "pc_sperren": {"what": "Den Computer sperren", "not_for": "Ein Programm schließen", "examples": ["sperr den pc", "computer sperren"]},
    # App-übergreifend: wirkt in jedem Programm, nicht nur in den in config.json eingetragenen
    "app_wechseln": {"what": "Zu einem bereits offenen Programm oder Fenster wechseln, es nach vorne holen",
                     "examples": ["wechsel zu discord", "zeig mir claude", "geh zu spotify", "hol brave nach vorne"]},
    "text_schreiben": {"what": "Einen Text in ein Programm tippen, in das gerade aktive oder in ein genanntes (Claude, Editor, Word, Browser)",
                       "not_for": "Eine Discord-Nachricht an eine Person oder in einen Kanal",
                       "examples": ["schreib in claude wie funktioniert eine for schleife", "tippe hallo zusammen",
                                    "schreib in den editor einkaufsliste"]},
    "taste_druecken": {"what": "Eine einzelne Taste oder Tastenkombination drücken",
                       "examples": ["drück enter", "alt tab", "strg z", "drück escape"]},
    # SteelSeries-Geräte (gear.py)
    "geraet_status": {"what": "Zustand der Geräte abfragen: Akkustand der Maus, eingestellte Sensi/DPI, Lautstärken der Mixer-Kanäle",
                      "examples": ["wie viel akku hat meine maus", "welche sensi hab ich", "wie stehen meine kanäle"]},
    "kanal_lautstaerke": {"what": "Die Lautstärke eines einzelnen Kanals im SteelSeries-Mixer setzen oder ändern",
                          "not_for": "Die allgemeine PC-Lautstärke (dafür lauter/leiser)",
                          "examples": ["mikrofon auf fünfzig", "mach den chat kanal lauter", "medien leiser im mixer"]},
    "kanal_stumm": {"what": "Einen Kanal im SteelSeries-Mixer stumm schalten oder wieder anschalten",
                    "not_for": "Das Mikrofon in Discord (dafür discord_mikro)",
                    "examples": ["mikrofon im mixer stumm", "medien kanal stumm"]},
    "maus_sensi": {"what": "Die Sensitivität / DPI der Maus umstellen",
                   "examples": ["sensi auf sechzehnhundert", "dpi auf 800", "stell die maus auf 3200 dpi"]},
    # Fragen beantworten (answers.py)
    "wetter": {"what": "Nach dem Wetter fragen, für heute, morgen oder einen genannten Ort",
               "not_for": "Im Browser oder Internet nach dem Wetter suchen",
               "examples": ["wie wird das wetter morgen", "wetter in köln", "regnet es heute"]},
    "rechnen": {"what": "Eine Rechenaufgabe ausrechnen",
                "examples": ["was ist siebzehn mal dreiundzwanzig", "zwanzig prozent von 250"]},
    "suchen": {"what": "Nach etwas suchen: auf YouTube, im Internet/Browser, in Spotify, nach Dateien auf dem PC oder in einem anderen Programm",
               "not_for": "Musik direkt abspielen (dafür spotify_abspielen)",
               "examples": ["such auf youtube nach minecraft tutorials", "google wie hoch ist der eiffelturm",
                            "such in spotify nach apache 207", "such im explorer nach bewerbung", "such hier nach preis"]},
    "claude_fragen": {"what": "Eine Wissensfrage, Erklärung, Übersetzung, ein Rat oder eine Unterhaltung: etwas, das man beantworten muss statt am PC auszuführen",
                      "not_for": "Wetter, Rechenaufgaben, Uhrzeit oder welcher Song läuft (dafür gibt es eigene Absichten)",
                      "examples": ["wer hat die glühbirne erfunden", "erklär mir was ein schwarzes loch ist",
                                   "was heißt danke auf japanisch", "was soll ich heute kochen", "frag claude wie lange nudeln kochen"]},
    "sonstiges": {"what": "Etwas anderes, das in keine dieser Kategorien passt, oder unverständliche Wörter"},
}

SUCH_ORTE = {
    "youtube": {"what": "Videos auf YouTube", "examples": ["such auf youtube nach katzenvideos", "youtube minecraft tutorial"]},
    "google": {"what": "Allgemein im Internet, im Browser oder mit Google, wenn keine andere Seite genannt ist",
               "examples": ["google wie hoch ist der eiffelturm", "such im internet nach pizza rezept", "such im browser nach wetter köln"]},
    "spotify": {"what": "Songs, Künstler oder Podcasts in Spotify suchen", "examples": ["such in spotify nach apache 207"]},
    "twitch": {"what": "Streams oder Streamer auf Twitch", "examples": ["such auf twitch nach papaplatte"]},
    "netflix": {"what": "Filme oder Serien auf Netflix", "examples": ["such auf netflix nach dark"]},
    "amazon": {"what": "Produkte auf Amazon", "examples": ["such auf amazon nach einer maus"]},
    "wikipedia": {"what": "Einen Artikel auf Wikipedia", "examples": ["such auf wikipedia nach albert einstein"]},
    "pc_dateien": {"what": "Dateien oder Ordner auf dem PC, im Explorer", "examples": ["such im explorer nach bewerbung", "such auf dem pc nach dem foto"]},
    "programm": {"what": "In einem anderen offenen Programm (z. B. Discord, Editor, VS Code) oder im gerade aktiven Fenster (\"hier\", \"auf dieser Seite\")",
                 "examples": ["such in discord nach max", "such hier nach preis", "such auf dieser seite nach kontakt"]},
}

# Suchbegriff aus dem Satz schneiden: Verb, Ortsangabe und "nach" weg
_SUCH_VERB = (r"(such(e|t)?|durchsuch(e)?|google|googel|googeln|googlen|googlet|guugel|find(e)?|zeig( mir)?"
              r"|schau( mal)?|guck( mal)?)")
_HIER = r"(hier|auf dieser seite|auf der seite|in diesem fenster|in dem fenster|auf dem bildschirm)"
_EXTRA_ORTE = ["browser", "internet", "netz", "web", "pc", "computer", "festplatte", "explorer", "dateien"]


def _ort_woerter():
    woerter = set(_EXTRA_ORTE) | (set(SUCH_ORTE) - {"programm", "pc_dateien"})
    for schluessel, eintrag in (*CONFIG["apps"].items(), *CONFIG["webseiten"].items()):
        woerter.add(schluessel.replace("_", " "))
        woerter.update(eintrag.get("woerter", []))
    return sorted(woerter, key=len, reverse=True)


def suchbegriff(text):
    """'such auf youtube nach minecraft tutorials' -> 'minecraft tutorials'. -> str"""
    t = re.sub(r"[.!?]+$", "", text.strip()).strip()
    t = re.sub(r"^(hey\s+)?(jeff|jev)[,\s]+", "", t, flags=re.I)
    t = re.sub(r"^(bitte|mal|kannst du( mal)?|könntest du( mal)?)\s+", "", t, flags=re.I)
    t = re.sub(rf"^{_SUCH_VERB}\b[,\s]*((mal|bitte|doch)\s+)*", "", t, flags=re.I)
    orte = "|".join(re.escape(w) for w in _ort_woerter())
    ortsangabe = rf"\b(auf|in|im|bei|über|mit|unter)\s+((dem|der|den|die|das|meinem|meiner)\s+)?({orte})\w*(\s+(app|seite))?\b"
    t = re.sub(ortsangabe, " ", t, flags=re.I)
    t = re.sub(rf"\b{_HIER}\b", " ", t, flags=re.I)
    t = re.sub(rf"^({orte})\w*\b", "", t.strip(), flags=re.I)          # "youtube katzenvideos"
    # unbekanntes Programm vor "nach": "in obsidian nach x" -> "x"
    t = re.sub(r"^(auf|in|im|bei)\s+\S+(\s+\S+)?\s+nach\s+", "", t.strip(), flags=re.I)
    t = re.sub(r"^(nach|für|zu)\s+", "", t.strip(), flags=re.I)
    t = re.sub(r"^(ein|eine|einer|einem|einen)\s+", "", t.strip(), flags=re.I)
    t = re.sub(r"\s+(bitte|mal)$", "", t.strip(), flags=re.I)
    t = re.sub(r"\s+(suchen|googeln|finden|raus)$", "", t.strip(), flags=re.I)
    return re.sub(r"\s+", " ", t).strip(" ,")


def ist_spiel(w):
    """Spiele bekommen keine Tastendrücke: Steam-Spiele und die in config.json eingetragenen."""
    exe = fenster.pfad(w["hwnd"]).lower()
    return "\\steamapps\\" in exe or w["prozess"].lower() in {s.lower() for s in CONFIG.get("spiele", [])}


def such_ziel(text):
    """Genanntes Programm in 'such in obsidian nach x' -> 'obsidian'. -> str|None"""
    m = re.search(r"\b(in|im|bei)\s+((dem|der|den|meinem)\s+)?(\S+(?:\s+\S+)?)\s+nach\b", text, re.I)
    if not m:
        m = re.search(r"\b(in|im|bei)\s+((dem|der|den|meinem)\s+)?(\S+)[.!?]?\s*$", text, re.I)
    return m.group(4).strip(".,!?") if m else None

# Kanäle des SteelSeries-Mixers für die Jev-Frage
KANAELE = {
    "master": "Gesamtlautstärke / Kopfhörer / alles",
    "mikrofon": "Das eigene Mikrofon",
    "chat": "Stimmen der anderen im Sprachchat",
    "spiel": "Der Ton des Spiels",
    "medien": "Musik, YouTube, Videos",
    "aux": "Der Aux-Kanal",
}

SPOTIFY_ARTEN = {
    "song": {"what": "Ein bestimmter einzelner Song", "examples": ["spiel bohemian rhapsody", "spiel den song roller"]},
    "kuenstler": {"what": "Musik von einem Künstler oder einer Band", "examples": ["spiel was von apache 207", "spiel die beatles"]},
    "album": {"what": "Ein ganzes Album", "examples": ["spiel das album zwei seiten"]},
    "eigene_playlist": {"what": "Eine eigene oder gespeicherte Playlist der Person", "examples": ["spiel meine gym playlist", "spiel meine chill playlist"]},
    "lieblingssongs": {"what": "Die gelikten Songs, also die Lieblingssongs der Person", "examples": ["spiel meine lieblingssongs", "spiel meine gelikten songs"]},
    "playlist_suche": {"what": "Eine fremde Playlist zu einer Stimmung oder einem Genre", "not_for": "Eine Playlist, die die Person als ihre eigene bezeichnet", "examples": ["spiel eine playlist zum lernen", "spiel deutschrap"]},
}

DISCORD_ZIELE = {
    "kanal": {"what": "Ein Textkanal auf einem Server", "examples": ["öffne den gaming kanal", "schreib in general"]},
    "sprachkanal": {"what": "Ein Sprachkanal, den die Person betreten will", "examples": ["tritt dem zocken sprachkanal bei", "join voice"]},
    "person": {"what": "Ein Direktchat mit einer einzelnen Person", "examples": ["schreib max", "öffne den chat mit lisa"]},
    "server": {"what": "Ein ganzer Server", "examples": ["öffne den server von der klasse"]},
}

HINWEIS_ASR = "Der Text stammt aus einer automatischen Spracherkennung und kann einzelne falsch erkannte Wörter enthalten."

# Wörter, die das Weckwort-Modell kennen soll: Befehle, Zahlen und Alltagswörter.
# Die Alltagswörter verhindern, dass normale Sätze fälschlich als Weckwort gelten.
GRUND_WORTSCHATZ = """
öffne öffnen starte starten mach mache auf zu schließe schließen beende beenden geh gehe zeig zeige mir
lauter leiser ton stumm aus an wieder musik pause weiter spiel spiele stopp stop halt
nächste nächstes nächster vorherige vorheriges vorheriger lied song zurück überspringen
timer wecker stell stelle setz setze für in minute minuten sekunde sekunden stunde stunden halbe halb viertel
wie spät ist es uhrzeit uhr sperr sperre sperren computer pc bildschirm programm seite webseite
ein eins eine einen zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn vierzehn fünfzehn
sechzehn siebzehn achtzehn neunzehn zwanzig dreißig vierzig fünfzig sechzig und
der die das den dem ich du er sie wir ihr nicht mit von zu im hat habe haben war was wer wo wann warum
ja nein hallo frau herr chef jens heute morgen gestern gut schlecht geht gehen los lass uns mich dich
kommt kommen später früher keine kein lust zeit mal noch schon auch aber oder wenn dann so da hier dort
mehr sehr viel angerufen anrufen müller schmidt jetzt jede jeder schiff schaf gib weg wach ach okay bitte danke
playlist mikro mikrofon kanal server nachricht nachrichten schreib schreibe neues gibt lies vor gerade läuft
gefällt speicher zufall senden abschicken schick abbrechen genau richtig falsch meine
""".split()

JA_WOERTER = {"ja", "senden", "abschicken", "schick", "genau", "okay", "richtig", "los"}
NEIN_WOERTER = {"nein", "abbrechen", "stopp", "stop", "falsch", "halt"}

# Typische Whisper-Erfindungen bei Stille oder Rauschen
HALLUZINATIONEN = ("untertitel", "amara.org", "vielen dank fürs zuschauen", "danke fürs zuschauen", "swr", "zdf")

ZAHLWOERTER = {
    "ein": 1, "eins": 1, "eine": 1, "einen": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6,
    "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12, "dreizehn": 13, "vierzehn": 14,
    "fünfzehn": 15, "sechzehn": 16, "siebzehn": 17, "achtzehn": 18, "neunzehn": 19, "zwanzig": 20,
    "dreißig": 30, "vierzig": 40, "fünfzig": 50, "sechzig": 60,
}


def zahl_aus_text(text):
    """Erste Zahl im Text: Ziffern oder Zahlwort, auch 'sechzehnhundert' (DPI). -> float|None"""
    m = re.search(r"\d+(?:[.,]\d+)?", text)
    if m:
        return float(m.group().replace(",", "."))
    for wort in re.sub(r"[.,!?]", " ", text.lower()).split():
        if wort in ZAHLWOERTER:
            return float(ZAHLWOERTER[wort])
        h = re.fullmatch(r"(\w+?)hundert", wort)
        if h and h.group(1) in ZAHLWOERTER:
            return float(ZAHLWOERTER[h.group(1)] * 100)
        t = re.fullmatch(r"(\w*?)tausend", wort)
        if t:
            return float(ZAHLWOERTER.get(t.group(1), 1) * 1000)
    return None


# gesprochene Tastennamen -> Kürzel für tastatur.druecke
_TASTENNAMEN = {"steuerung": "ctrl", "strg": "ctrl", "control": "ctrl", "kontrolle": "ctrl",
                "umschalt": "shift", "shift": "shift", "alt": "alt", "windows": "win", "win": "win",
                "eingabe": "enter", "enter": "enter", "return": "enter", "escape": "esc", "esc": "esc",
                "tab": "tab", "tabulator": "tab", "leertaste": "space", "space": "space",
                "rücktaste": "backspace", "backspace": "backspace", "entfernen": "delete", "delete": "delete",
                **{f"f{n}": f"f{n}" for n in range(1, 13)}}


def tasten_aus_text(text):
    """'drück strg z' -> 'ctrl+z'; 'alt tab' -> 'alt+tab'. -> str|None"""
    roh = re.sub(r"^\s*(drück(e)?|drucke|tipp(e)?|taste)\s+", "", text.strip(), flags=re.I)
    teile = []
    for wort in re.sub(r"[.,!?]", " ", roh.lower()).replace("+", " ").split():
        if wort in _TASTENNAMEN:
            teile.append(_TASTENNAMEN[wort])
        elif len(wort) == 1 and wort.isalnum():
            teile.append(wort)
        elif teile:
            break  # nach der Kombination kommt anderer Text
    if not teile:
        return None
    # Reihenfolge: Zusatztasten zuerst
    rang = {"ctrl": 0, "shift": 1, "alt": 2, "win": 3}
    teile.sort(key=lambda t: rang.get(t, 9))
    return "+".join(dict.fromkeys(teile))


def app_eintrag(name):
    """config.json-Eintrag zu einem gesprochenen Programmnamen. -> (schluessel, eintrag)|None"""
    n = (name or "").lower()
    for schluessel, app in CONFIG["apps"].items():
        if schluessel in n or any(w in n for w in app["woerter"]):
            return schluessel, app
    return None


def fenster_fuer_ziel(ziel):
    """Fenster zu einem gesprochenen Namen finden.

    Erst direkt nach dem Namen suchen, dann ueber config.json: "Editor" heisst in
    Windows 11 "Notepad", im Fenstertitel steht das gesprochene Wort also nicht.
    """
    treffer = fenster.suche(ziel)
    if treffer:
        return treffer
    eintrag = app_eintrag(ziel)
    if not eintrag:
        return None
    schluessel, app = eintrag
    # Kandidaten: Prozessname, Startdatei ("notepad.exe" -> "notepad"), Stichwörter, Schlüssel
    kandidaten = [app.get("prozess", ""), os.path.basename(app.get("start", "")), *app["woerter"], schluessel]
    for name in kandidaten:
        name = name.replace(".exe", "").strip()
        if len(name) >= 3:
            treffer = fenster.suche(name)
            if treffer:
                return treffer
    return None


def schreib_zerlegen(text):
    """'schreib in claude wie geht das' -> ('claude', 'wie geht das').

    Das Ziel wird gegen die wirklich offenen Fenster geprueft, damit aus
    'schreib in den editor ...' nicht das Ziel 'den' wird.
    """
    rest = re.sub(r"^\s*(schreib(e)?|tipp(e)?|gib ein|schreib mal)\s*", "", text.strip(), flags=re.I)
    m = re.match(r"^(in das|in den|in die|ins|in|beim|bei|auf|an)\s+(.+)$", rest, re.I)
    if not m:
        return None, rest.strip()
    worte = re.sub(r"^(den|die|das|dem|meinem|meiner|mein)\s+", "", m.group(2), flags=re.I).split()

    def inhalt_ab(anzahl):
        inhalt = re.sub(r"^(dass|das|folgendes|rein)\s+", "", " ".join(worte[anzahl:]), flags=re.I)
        return inhalt.strip()

    for anzahl in (3, 2, 1):                      # offenes Fenster hat Vorrang
        if len(worte) > anzahl and fenster.suche(" ".join(worte[:anzahl])):
            return " ".join(worte[:anzahl]), inhalt_ab(anzahl)
    for anzahl in (1, 2):                         # sonst ein eingetragenes Programm, das noch nicht laeuft
        name = " ".join(worte[:anzahl]).lower()
        for app in CONFIG["apps"].values():
            if any(w in name for w in app["woerter"]) and len(worte) > anzahl:
                return name, inhalt_ab(anzahl)
    return None, rest.strip()


def api_key():
    """Liest den Key aus der Benutzer-Umgebung, damit ein neuer setx-Wert ohne Neustart greift."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, "TYPESAFE_API_KEY")[0]
    except OSError:
        return os.environ.get("TYPESAFE_API_KEY")


def wortschatz():
    woerter = set(GRUND_WORTSCHATZ)
    for eintrag in (*CONFIG["apps"].values(), *CONFIG["webseiten"].values()):
        woerter.update(eintrag["woerter"])
    return [CONFIG["weckwort"], *sorted(woerter), "[unk]"]


def dauer_sekunden(text):
    """Liest eine Dauer wie "fünf minuten" oder "halbe stunde" aus dem Text."""
    woerter = re.sub(r"[.,!?]", " ", text.lower()).split()
    if "halbe" in woerter and any(w.startswith("stunde") for w in woerter):
        return 1800
    for i, wort in enumerate(woerter):
        zahl = int(wort) if wort.isdigit() else ZAHLWOERTER.get(wort)
        if zahl is None:
            continue
        # "einen timer": Artikel, keine Zahl – außer direkt vor einer Einheit ("eine minute")
        if wort.startswith("ein") and not re.match(r"(sekunde|minute|stunde)", woerter[i + 1] if i + 1 < len(woerter) else ""):
            continue
        # "fünf und zwanzig" -> 25
        if i + 2 < len(woerter) and woerter[i + 1] == "und" and ZAHLWOERTER.get(woerter[i + 2], 0) >= 20:
            zahl += ZAHLWOERTER[woerter[i + 2]]
        einheit = " ".join(woerter[i + 1:i + 4])
        if "sekunde" in einheit:
            return zahl
        if "stunde" in einheit:
            return zahl * 3600
        return zahl * 60
    return None


def dauer_text(sekunden):
    if sekunden % 3600 == 0:
        return f"{sekunden // 3600} Stunde" + ("n" if sekunden > 3600 else "")
    if sekunden % 60 == 0:
        return f"{sekunden // 60} Minute" + ("n" if sekunden > 60 else "")
    return f"{sekunden} Sekunden"


class Sprecher:
    """Sprachausgabe in eigenem Thread; solange sie spricht, hört das Mikrofon nicht zu."""

    def __init__(self, aktiv):
        self.aktiv = aktiv
        self.spricht = threading.Event()
        self.warteschlange = queue.Queue()
        if aktiv:
            threading.Thread(target=self._schleife, daemon=True).start()

    def sage(self, text):
        log.info("Ansage: %s", text)
        if self.aktiv:
            self.spricht.set()
            self.warteschlange.put(text)

    def _schleife(self):
        import pyttsx3
        engine = pyttsx3.init()
        for stimme in engine.getProperty("voices"):
            if "German" in stimme.name or "Deutsch" in stimme.name:
                engine.setProperty("voice", stimme.id)
                break
        while True:
            text = self.warteschlange.get()
            self.spricht.set()
            engine.say(text)
            engine.runAndWait()
            time.sleep(0.3)
            if self.warteschlange.empty():
                self.spricht.clear()


def ton(art):
    tonfolgen = {"wach": [(880, 120)], "ok": [(1320, 80)], "fehler": [(300, 250)], "alarm": [(1000, 300), (0, 150)] * 4}
    def spielen():
        for freq, ms in tonfolgen[art]:
            time.sleep(ms / 1000) if freq == 0 else winsound.Beep(freq, ms)
    threading.Thread(target=spielen, daemon=True).start()


class Audiopuffer:
    """Merkt sich die letzten Sekunden Audio, damit Whisper den Befehl nachträglich bekommt."""

    def __init__(self, rate, sekunden=30):
        self.rate = rate
        self.daten = bytearray()
        self.start = 0  # Sample-Nummer von daten[0], gezählt ab Beginn des Streams
        self.max_bytes = rate * sekunden * 2

    def dazu(self, block):
        self.daten += block
        zuviel = len(self.daten) - self.max_bytes
        if zuviel > 0:
            zuviel -= zuviel % 2
            del self.daten[:zuviel]
            self.start += zuviel // 2

    def ausschnitt(self, von, bis):
        """Audio zwischen zwei Zeitpunkten (Sekunden, wie Vosk sie liefert) als 16-kHz-float32."""
        a = max(0, int(von * self.rate) - self.start) * 2
        b = max(0, int(bis * self.rate) - self.start) * 2
        roh = np.frombuffer(bytes(self.daten[a:b]), dtype=np.int16).astype(np.float32) / 32768
        if self.rate != 16000 and len(roh):
            n = int(len(roh) * 16000 / self.rate)
            roh = np.interp(np.linspace(0, len(roh) - 1, n), np.arange(len(roh)), roh).astype(np.float32)
        return roh


class Assistent:
    def __init__(self, trocken=False, sprachausgabe=True, mit_whisper=True):
        from typesafe_sdk import TypeSafeClient

        self.trocken = trocken
        self.client = TypeSafeClient(api_key=api_key())
        self.sprecher = Sprecher(sprachausgabe and CONFIG["sprachausgabe"])
        self.wartet_bis = None
        self.bestaetigung = None

        self.whisper = None
        if mit_whisper:
            self.whisper = self._whisper_laden()

        self.spotify = None
        if CONFIG["spotify"]["client_id"]:
            self.spotify = spotify_steuerung.Spotify(CONFIG["spotify"]["client_id"], SPOTIFY_TOKEN,
                                                     os.path.expandvars(CONFIG["apps"]["spotify"]["start"]))
            if self.spotify.angemeldet():
                threading.Thread(target=self._playlists_laden, daemon=True).start()
            else:
                log.warning("Spotify nicht angemeldet. Einmalig ausführen: python jev_assistent.py --spotify-login")
                self.spotify = None

        self.discord = discord_steuerung.Discord(CONFIG["discord"], CONFIG["apps"]["discord"])
        self.benachrichtigungen = discord_steuerung.Benachrichtigungen()
        self.benachrichtigungen.start()

    def _whisper_laden(self):
        """Whisper laden - bevorzugt auf der zweiten GPU (RTX 3050), damit die
        RTX 5070 fuer Spiele frei bleibt. Ohne nutzbare GPU faellt es auf die CPU zurueck."""
        from faster_whisper import WhisperModel

        ordner = str(BASIS / "whisper-modelle")
        gpu = CONFIG.get("whisper_gpu", 1)
        if gpu is not None:
            try:
                modell = WhisperModel(CONFIG["whisper_modell"], device="cuda", device_index=gpu,
                                      compute_type="float16", download_root=ordner)
                # cuBLAS wird erst beim ersten Rechnen geladen - fehlt es, soll das hier auffallen
                list(modell.transcribe(np.zeros(16000, dtype=np.float32), language="de")[0])
                log.info("Whisper laeuft auf GPU %s (%s)", gpu, CONFIG["whisper_modell"])
                return modell
            except Exception as e:  # noqa: BLE001 - jede GPU-Macke faellt auf CPU zurueck
                log.warning("Whisper auf GPU %s nicht moeglich (%s), nutze CPU", gpu, e)
        log.info("Whisper laeuft auf der CPU (%s)", CONFIG["whisper_modell"])
        return WhisperModel(CONFIG["whisper_modell"], device="cpu", compute_type="int8",
                            cpu_threads=4, download_root=ordner)

    def _playlists_laden(self):
        try:
            log.info("%d Spotify-Playlists geladen", len(self.spotify.playlists()))
        except Exception as e:
            log.warning("Spotify-Playlists nicht ladbar: %s", e)

    # --- Spracheingabe -------------------------------------------------

    def gehoert(self, ergebnis, puffer):
        """Wird für jeden Satz aufgerufen, den Vosk abgeschlossen hat."""
        woerter = ergebnis.get("result", [])
        if not woerter:
            return
        text = " ".join(w["word"] for w in woerter if w["word"] != "[unk]")
        log.debug("gehört: %s", text or "[unverständlich]")
        jetzt = time.monotonic()
        wach = self._weckwort_ende(woerter)

        if self.bestaetigung and wach is None:
            self._bestaetigung_beantworten(set(text.split()))
            return

        if wach is not None:
            if self.bestaetigung:
                self._bestaetigung_beenden(senden=False)
            log.info("Weckwort erkannt")
            rest = woerter[wach + 1:]
            if rest:
                self.befehl_aus_audio(puffer, woerter[wach]["end"], rest[-1]["end"], self._text(rest))
            else:
                ton("wach")
                self.wartet_bis = jetzt + CONFIG["wartezeit_befehl_sekunden"]
        elif self.wartet_bis and jetzt < self.wartet_bis:
            self.wartet_bis = None
            self.befehl_aus_audio(puffer, woerter[0]["start"], woerter[-1]["end"], text)

    @staticmethod
    def _text(woerter):
        return " ".join(w["word"] for w in woerter if w["word"] != "[unk]")

    @staticmethod
    def _weckwort_ende(woerter):
        teile = CONFIG["weckwort"].split()
        for i in range(len(woerter) - len(teile) + 1):
            if [w["word"] for w in woerter[i:i + len(teile)]] == teile:
                return i + len(teile) - 1
        return None

    def befehl_aus_audio(self, puffer, von, bis, vosk_text):
        audio = puffer.ausschnitt(von - 0.1, bis + 0.5)
        self._speichern(audio)
        text = self.transkribiere(audio)
        if not text and not vosk_text:
            ton("fehler")
            log.info("Whisper hat nichts verstanden")
            return None
        return self.befehl(text or vosk_text, alternativ=vosk_text)

    @staticmethod
    def _speichern(audio):
        """Letzten Befehl als WAV ablegen, um Erkennungsfehler nachhören zu können."""
        with wave.open(str(BASIS / "letzter_befehl.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())

    def transkribiere(self, audio):
        segmente, _ = self.whisper.transcribe(
            audio, language="de", beam_size=5, condition_on_previous_text=False,
            initial_prompt=self._whisper_hinweis())
        text = " ".join(s.text.strip() for s in segmente if s.no_speech_prob < 0.6).strip()
        if any(h in text.lower() for h in HALLUZINATIONEN):
            return ""
        # Reste des Weckworts am Anfang entfernen ("Yif! Spiel ..." -> "Spiel ...")
        return re.sub(r"^\W*((hey|hei|hay|he)\W*)?(jev|jeff|jef|yif|yiff|if|jeb|chef)\b\W*", "", text, flags=re.IGNORECASE)

    def _whisper_hinweis(self):
        namen = ["Spotify", "Discord", "Playlist"]
        if self.spotify:
            namen += list(self.spotify._playlists)[:30]
        namen += list(CONFIG["discord"].get("namen", {}))
        return ", ".join(namen)[:400] + "."

    # --- Jev fragen ----------------------------------------------------

    def frage_jev(self, text, alternativ=None):
        from typesafe_sdk import Choice, Noul

        zustand = {"befehl": text}
        hinweis = HINWEIS_ASR
        if alternativ and alternativ.lower() != text.lower():
            zustand["befehl_alternativ"] = alternativ
            hinweis += (" `befehl_alternativ` ist eine zweite, unabhängige Erkennung desselben Satzes mit kleinem Wortschatz;"
                        " wo `befehl` keinen Sinn ergibt, kann sie das Gemeinte zeigen.")

        def frage(q):
            return {"question": q, "note": hinweis}

        apps = {name: a["beschreibung"] for name, a in CONFIG["apps"].items()}
        apps["keins"] = "Der Befehl nennt kein Programm aus dieser Liste"
        seiten = {name: s["beschreibung"] for name, s in CONFIG["webseiten"].items()}
        seiten["keine"] = "Der Befehl nennt keine Webseite aus dieser Liste"

        # Alle Fragen in einer Anfrage; der Code nutzt nur die, die zur Absicht passen.
        fragen = {
            "absicht": Choice(instructions=frage("Was möchte die Person mit dem gesprochenen Befehl in `befehl` am PC erreichen?"), criteria=ABSICHTEN),
            "app": Choice(instructions=frage("Welches Programm nennt der gesprochene Befehl in `befehl`?"), criteria=apps),
            "webseite": Choice(instructions=frage("Welche dieser Webseiten will die Person mit dem gesprochenen Befehl in `befehl` aufrufen?"), criteria=seiten),
            "spotify_art": Choice(instructions=frage("Was soll laut `befehl` auf Spotify abgespielt werden?"), criteria=SPOTIFY_ARTEN),
            "shuffle_an": Noul(instructions=frage("Soll laut `befehl` die Zufallswiedergabe eingeschaltet werden, nicht ausgeschaltet?")),
            "discord_ziel": Choice(instructions=frage("Wohin in Discord will die Person laut `befehl`?"), criteria=DISCORD_ZIELE),
            "such_ort": Choice(instructions=frage("Angenommen, die Person will laut `befehl` nach etwas suchen: wo?"),
                               criteria=SUCH_ORTE),
            "kanal": Choice(instructions=frage("Angenommen, `befehl` meint einen Kanal des SteelSeries-Mixers "
                                               "(lauter, leiser, stumm). Welchen? Ohne Nennung: master."),
                            criteria=KANAELE),
        }
        # offene Fenster als Auswahl: damit wirkt der Assistent in jedem Programm
        self._fenster = fenster.liste()
        if self._fenster:
            optionen = {f"w{i}": f"{w['titel'][:70]} ({w['prozess']})" for i, w in enumerate(self._fenster)}
            optionen["keins"] = "Der Befehl nennt keines dieser offenen Fenster"
            zustand["aktives_fenster"] = fenster.aktives()["titel"]
            fragen["fenster"] = Choice(instructions=frage("Welches dieser offenen Fenster meint der gesprochene "
                                                          "`befehl` (zum Hinwechseln oder Hineinschreiben)?"),
                                       criteria=optionen)
        playlists = list(self.spotify._playlists)[:100] if self.spotify else []
        if playlists:
            optionen = {f"p{i}": name for i, name in enumerate(playlists)}
            optionen["keine"] = "Keine dieser Playlists"
            fragen["playlist"] = Choice(instructions=frage("Welche dieser eigenen Spotify-Playlists meint der gesprochene Befehl in `befehl`?"), criteria=optionen)

        antwort = self.client.system_one(state=zustand, questions=fragen)
        return antwort.answers, playlists

    def treffer_waehlen(self, wunsch, treffer, art):
        """Jev wählt aus den Spotify-Suchergebnissen den gemeinten Treffer."""
        from typesafe_sdk import Choice

        if len(treffer) == 1:
            return treffer[0]
        optionen = {f"t{i}": spotify_steuerung.beschreibe(t, art) for i, t in enumerate(treffer)}
        optionen["keiner"] = "Keiner dieser Treffer passt zum Wunsch"
        wahl = self.client.system_one(
            state={"wunsch": wunsch},
            questions={"treffer": Choice(
                instructions={"question": "Welcher Spotify-Treffer passt zu dem gesprochenen Musikwunsch in `wunsch`?", "note": HINWEIS_ASR},
                criteria=optionen)},
        ).answers["treffer"]
        log.info("Jev: treffer=%s (%.2f)", wahl.choice, wahl.confidence)
        if wahl.choice == "keiner":
            return None if wahl.confidence >= 0.6 else treffer[0]
        return treffer[int(wahl.choice[1:])]

    # --- Befehle ausführen ---------------------------------------------

    def befehl(self, text, alternativ=None, von_claude=False):
        log.info("Befehl: %s%s", text, f"  (Vosk: {alternativ})" if alternativ else "")
        try:
            a, playlists = self.frage_jev(text, alternativ)
        except Exception as e:
            log.error("Jev-Anfrage fehlgeschlagen: %s", e)
            ton("fehler")
            self.sprecher.sage("Ich erreiche Jev gerade nicht.")
            return None

        absicht, sicherheit = a["absicht"].choice, a["absicht"].confidence
        log.info("Jev: absicht=%s (%.2f) app=%s (%.2f) webseite=%s (%.2f) spotify=%s (%.2f) discord=%s (%.2f)",
                 absicht, sicherheit, a["app"].choice, a["app"].confidence, a["webseite"].choice, a["webseite"].confidence,
                 a["spotify_art"].choice, a["spotify_art"].confidence, a["discord_ziel"].choice, a["discord_ziel"].confidence)

        schwellen = CONFIG["schwellen"]
        if absicht == "claude_fragen" and sicherheit >= schwellen["absicht"] and not von_claude:
            return self.claude_verstehen(text, alternativ)
        if absicht in ("sonstiges", "claude_fragen") or sicherheit < schwellen["absicht"]:
            # Jev versteht es nicht: Claude den Satz deuten lassen (nur einmal, keine Schleife)
            if not von_claude and CONFIG.get("claude", {}).get("aktiv"):
                return self.claude_verstehen(text, alternativ)
            return self._fehler("Das habe ich nicht verstanden.", "nicht_verstanden")
        if absicht == "pc_sperren" and sicherheit < schwellen["pc_sperren"]:
            return self._fehler("Soll ich den PC sperren? Sag es bitte noch einmal deutlich.", "nicht_sicher")

        try:
            if absicht.startswith("spotify_"):
                ergebnis = self.spotify_befehl(absicht, text, a, playlists)
            elif absicht.startswith("discord_"):
                ergebnis = self.discord_befehl(absicht, text, a)
            else:
                ergebnis = self.pc_befehl(absicht, text, a)
        except Exception as e:
            log.exception("Befehl fehlgeschlagen")
            return self._fehler("Das hat leider nicht geklappt.", f"fehler:{e}")
        return ergebnis

    def _fehler(self, ansage, ergebnis):
        ton("fehler")
        self.sprecher.sage(ansage)
        return ergebnis

    def _fertig(self, ergebnis, ansage=None):
        if self.trocken:
            log.info("[Trockenlauf] würde ausführen: %s", ergebnis)
        else:
            ton("ok")
            log.info("ausgeführt: %s", ergebnis)
        if ansage:
            self.sprecher.sage(ansage)
        return ergebnis

    def pc_befehl(self, absicht, text, a):
        schwelle = CONFIG["schwellen"]["ziel"]

        if absicht in ("app_oeffnen", "app_schliessen"):
            ziel = a["app"]
            if ziel.choice == "keins" or ziel.confidence < schwelle:
                # "öffne youtube" kann auch eine Webseite meinen
                if absicht == "app_oeffnen" and a["webseite"].choice != "keine" and a["webseite"].confidence >= schwelle:
                    return self.pc_befehl("webseite_oeffnen", text, a)
                return self._fehler("Welches Programm meinst du?", "ziel_unklar")
            app = CONFIG["apps"][ziel.choice]
            if absicht == "app_schliessen" and not app.get("prozess"):
                return self._fehler("Das kann ich nicht schließen.", "nicht_moeglich")
            if not self.trocken:
                if absicht == "app_oeffnen":
                    os.startfile(os.path.expandvars(app["start"]), arguments=app.get("argumente", ""))
                else:
                    subprocess.run(["taskkill", "/IM", app["prozess"]], capture_output=True)
            return self._fertig(f"{absicht}:{ziel.choice}")

        if absicht == "webseite_oeffnen":
            ziel = a["webseite"]
            if ziel.choice == "keine" or ziel.confidence < schwelle:
                return self._fehler("Welche Webseite meinst du?", "ziel_unklar")
            if not self.trocken:
                webbrowser.open(CONFIG["webseiten"][ziel.choice]["url"])
            return self._fertig(f"{absicht}:{ziel.choice}")

        if absicht in MEDIENTASTEN:
            if absicht == "musik_pause" and not self.trocken and not prozess_laeuft("Spotify.exe"):
                os.startfile(os.path.expandvars(CONFIG["apps"]["spotify"]["start"]))
                time.sleep(5)
            if not self.trocken:
                anzahl = CONFIG["lautstaerke_schritte"] if absicht in ("lauter", "leiser") else 1
                tastatur.druecke(MEDIENTASTEN[absicht], anzahl)
            return self._fertig(absicht)

        if absicht == "timer":
            sekunden = dauer_sekunden(text)
            if not sekunden:
                return self._fehler("Wie lange soll der Timer laufen?", "dauer_unklar")
            if not self.trocken:
                threading.Timer(sekunden, self.timer_abgelaufen).start()
            return self._fertig(f"timer:{sekunden}s", f"Timer läuft, {dauer_text(sekunden)}.")

        if absicht == "uhrzeit":
            jetzt = datetime.datetime.now()
            return self._fertig(absicht, f"Es ist {jetzt.hour} Uhr {jetzt.minute}.")

        if absicht == "pc_sperren":
            if not self.trocken:
                ctypes.windll.user32.LockWorkStation()
            return self._fertig(absicht)

        if absicht in ("app_wechseln", "text_schreiben", "taste_druecken"):
            return self.fenster_befehl(absicht, text, a)

        if absicht == "suchen":
            return self.such_befehl(text, a)

        if absicht in ("geraet_status", "kanal_lautstaerke", "kanal_stumm", "maus_sensi"):
            return self.geraet_befehl(absicht, text, a)

        if absicht in ("wetter", "rechnen"):
            if not answers:
                return self._fehler("Dafür fehlt mir das Antwort-Modul.", "modul_fehlt")
            try:
                antwort = answers.wetter(text) if absicht == "wetter" else answers.rechnen(text)
            except answers.AnswerError as e:
                return self._fehler(str(e), f"{absicht}_fehler")
            return self._fertig(absicht, antwort)

        return self._fehler("Das kann ich noch nicht.", "unbekannt")

    # --- Claude ---------------------------------------------------------
    def claude_verstehen(self, text, alternativ=None):
        """Claude deutet den Satz: klarer Befehl für Jeff (-> nochmal durch Jev) oder direkte Antwort."""
        ton("wach")  # Claude braucht ein paar Sekunden - kurzes Zeichen, dass Jeff arbeitet
        try:
            ergebnis = claude.frage(text, ABSICHTEN, alternativ, self._claude_kontext())
        except claude.ClaudeFehler as e:
            log.error("Claude nicht erreichbar: %s", e)
            return self._fehler("Das habe ich nicht verstanden.", "nicht_verstanden")
        log.info("Claude: %s", ergebnis)
        art = ergebnis.get("art")
        if art == "befehl" and ergebnis.get("befehl"):
            return self.befehl(ergebnis["befehl"], von_claude=True)
        if art == "antwort" and ergebnis.get("antwort"):
            return self._fertig("claude_antwort", ergebnis["antwort"])
        return self._fehler(ergebnis.get("antwort") or "Das habe ich nicht verstanden.", "claude_unklar")

    def _claude_kontext(self):
        kontext = {"aktives_fenster": fenster.aktives()["titel"][:80],
                   "offene_programme": sorted({w["prozess"] for w in fenster.liste()})[:25]}
        if self.spotify:
            kontext["spotify_playlists"] = list(self.spotify._playlists)[:40]
        if CONFIG["discord"].get("namen"):
            kontext["discord_namen"] = list(CONFIG["discord"]["namen"])
        return kontext

    # --- Suchen ---------------------------------------------------------
    def such_befehl(self, text, a):
        begriff = suchbegriff(text)
        ort, sicher = a["such_ort"].choice, a["such_ort"].confidence
        log.info("Suche: ort=%s (%.2f) begriff=%r", ort, sicher, begriff)
        if not begriff:
            return self._fehler("Wonach soll ich suchen?", "begriff_unklar")
        if sicher < CONFIG["schwellen"]["ziel"]:
            ort = "google"

        if ort == "spotify":
            if not self.trocken:
                os.startfile("spotify:search:" + urllib.parse.quote(begriff))
            return self._fertig(f"suchen:spotify:{begriff}")

        if ort == "pc_dateien":
            if not self.trocken:
                ordner = os.path.expanduser("~")
                os.startfile(f"search-ms:query={urllib.parse.quote(begriff)}&crumb=location:{urllib.parse.quote(ordner)}")
            return self._fertig(f"suchen:pc:{begriff}")

        if ort == "programm":
            return self._in_programm_suchen(text, begriff, a)

        seite = CONFIG["webseiten"].get(ort) or CONFIG["webseiten"]["google"]
        if not self.trocken:
            webbrowser.open(seite["suche"].format(urllib.parse.quote_plus(begriff)))
        return self._fertig(f"suchen:{ort}:{begriff}")

    def _in_programm_suchen(self, text, begriff, a):
        """Programm nach vorne holen, Suchfeld per Tastenkürzel öffnen, Begriff einfügen."""
        hier = re.search(rf"\b{_HIER}\b", text, re.I)
        w = None if hier else self._fenster_aus_antwort(a, text, such_ziel(text))
        if not w and not hier:
            return self._fehler("In welchem Programm soll ich suchen?", "fenster_fehlt")
        w = w or fenster.aktives()
        if ist_spiel(w):
            return self._fehler("Im Spiel tippe ich nichts.", "spiel_aktiv")
        # Programmname, der am Satzende hängen geblieben ist ("x in obsidian"), abschneiden
        for wort in re.findall(r"\w+", f"{w['titel']} {w['prozess']}".lower()):
            if len(wort) >= 3:
                begriff = re.sub(rf"\s+(in|im|bei|auf)\s+((dem|der)\s+)?{re.escape(wort)}\w*$", "", begriff, flags=re.I)
        eintrag = next((app for app in CONFIG["apps"].values()
                        if app.get("prozess", "").lower() == w["prozess"].lower()), {})
        taste = eintrag.get("suche_taste", "ctrl+f")
        if self.trocken:
            return self._fertig(f"suchen:{w['prozess']}:{taste}:{begriff}")
        if not hier and not fenster.nach_vorne(w["hwnd"]):
            return self._fehler(f"{w['titel'][:40]} lässt sich nicht nach vorne holen.", "fenster_blockiert")
        time.sleep(0.3)
        tastatur.druecke(taste)
        time.sleep(0.4)
        tastatur.einfuegen(begriff)
        time.sleep(0.1)
        tastatur.druecke("enter")
        return self._fertig(f"suchen:{w['prozess']}:{taste}:{begriff}")

    # --- App-übergreifend ----------------------------------------------
    def _fenster_aus_antwort(self, a, text, ziel=None):
        """Fenster bestimmen: ein im Satz genanntes Ziel schlägt Jevs Auswahl.

        Sonst landet "schreib in den editor ..." im gerade aktiven Fenster,
        weil Jev dieses für gemeint hält - der Text ginge ins falsche Programm.
        """
        if ziel:
            treffer = fenster_fuer_ziel(ziel)
            if treffer:
                return treffer
        wahl = a.get("fenster")
        if wahl is not None and wahl.choice != "keins" and wahl.confidence >= CONFIG["schwellen"]["ziel"]:
            i = int(wahl.choice[1:])
            if i < len(getattr(self, "_fenster", [])):
                gewaehlt = self._fenster[i]
                if not ziel:
                    return gewaehlt
                # Jevs Wahl nur nehmen, wenn sie zum genannten Ziel passt
                z = ziel.lower()
                if z in gewaehlt["titel"].lower() or z in gewaehlt["prozess"].lower():
                    return gewaehlt
        return None

    def fenster_befehl(self, absicht, text, a):
        if absicht == "app_wechseln":
            w = self._fenster_aus_antwort(a, text)
            if not w:
                # nicht offen: vielleicht ein eingetragenes Programm, das noch gestartet werden muss
                if a["app"].choice != "keins" and a["app"].confidence >= CONFIG["schwellen"]["ziel"]:
                    return self.pc_befehl("app_oeffnen", text, a)
                return self._fehler("Dieses Fenster ist nicht offen.", "fenster_fehlt")
            if not self.trocken and not fenster.nach_vorne(w["hwnd"]):
                return self._fehler(f"{w['titel'][:40]} lässt sich nicht nach vorne holen.", "fenster_blockiert")
            return self._fertig(f"app_wechseln:{w['prozess']}")

        if absicht == "taste_druecken":
            kombi = tasten_aus_text(text)
            if not kombi:
                return self._fehler("Welche Taste soll ich drücken?", "taste_unklar")
            if not self.trocken:
                tastatur.druecke(kombi)
            return self._fertig(f"taste_druecken:{kombi}")

        # text_schreiben
        ziel, inhalt = schreib_zerlegen(text)
        if not inhalt:
            return self._fehler("Was soll ich schreiben?", "text_unklar")
        w = self._fenster_aus_antwort(a, text, ziel) if ziel else None
        if ziel and not w and not self.trocken:
            w = self._app_starten_und_warten(ziel)    # Programm läuft noch nicht -> starten
        if ziel and not w:
            return self._fehler(f"Ein Fenster für {ziel} finde ich nicht.", "fenster_fehlt")
        if self.trocken:
            return self._fertig(f"text_schreiben:{ziel or 'aktives'}:{inhalt}")
        if w and not fenster.nach_vorne(w["hwnd"]):
            return self._fehler(f"{w['titel'][:40]} lässt sich nicht nach vorne holen.", "fenster_blockiert")
        time.sleep(0.2)
        tastatur.einfuegen(inhalt)
        # Absenden bleibt beim Nutzer: bei falsch erkanntem Text soll nichts rausgehen
        return self._fertig(f"text_schreiben:{(w or {}).get('prozess', 'aktives')}:{inhalt}",
                            "Getippt. Sag 'drück enter', wenn ich abschicken soll.")

    def _app_starten_und_warten(self, name, sekunden=8):
        """Eingetragenes Programm starten und auf sein Fenster warten. -> Fenster|None"""
        gefunden = app_eintrag(name)
        if not gefunden:
            return None
        eintrag = gefunden[1]
        try:
            os.startfile(os.path.expandvars(eintrag["start"]), arguments=eintrag.get("argumente", ""))
        except OSError as e:
            log.warning("Start von %s fehlgeschlagen: %s", name, e)
            return None
        ende = time.monotonic() + sekunden
        while time.monotonic() < ende:
            time.sleep(0.4)
            w = fenster.suche(eintrag.get("prozess", "").replace(".exe", "") or name)
            if w and fenster.nach_vorne(w["hwnd"]):
                time.sleep(0.5)   # Programm braucht einen Moment, bis es Eingaben annimmt
                return w
        return None

    # --- SteelSeries-Geräte --------------------------------------------
    def geraet_befehl(self, absicht, text, a):
        if not gear:
            return self._fehler("Dafür fehlt mir das Geräte-Modul.", "modul_fehlt")
        kanal = a["kanal"].choice if "kanal" in a else "master"
        zahl = zahl_aus_text(text)
        try:
            if absicht == "geraet_status":
                if re.search(r"akku|batterie|geladen|prozent.*maus", text, re.I):
                    akku = gear.akku()
                    if not akku:
                        return self._fertig(absicht, "Den Akkustand kann ich gerade nicht auslesen.")
                    return self._fertig(absicht, f"Die Maus hat {akku['prozent']} Prozent"
                                                 + (" und lädt." if akku["laedt"] else "."))
                if re.search(r"sensi|dpi|maus|polling|abfragerate", text, re.I):
                    m = gear.maus_status()
                    return self._fertig(absicht, f"{m['name']}: {m['dpi']} DPI bei {m['polling_hz']} Hertz.")
                zustand = gear.audio_status()
                return self._fertig(absicht, "; ".join(
                    f"{v['label']} {v['prozent']}" + (" stumm" if v["stumm"] else "") for v in zustand.values()))

            if absicht == "kanal_lautstaerke":
                if zahl is not None and re.search(r"\bauf\b|prozent", text, re.I):
                    neu = gear.audio_setzen(kanal, prozent=int(zahl))
                else:
                    jetzt = gear.audio_status().get(kanal, {})
                    richtung = -1 if re.search(r"leiser|runter|weniger", text, re.I) else 1
                    schritt = int(zahl) if zahl is not None else 10
                    neu = gear.audio_setzen(kanal, prozent=max(0, min(100, jetzt.get("prozent", 50)
                                                                      + richtung * schritt)))
                return self._fertig(f"{absicht}:{kanal}", f"{neu['label']} {neu['prozent']} Prozent.")

            if absicht == "kanal_stumm":
                if re.search(r"wieder an|nicht mehr stumm|unmute|anschalten", text, re.I):
                    neu = gear.audio_setzen(kanal, stumm=False)
                elif re.search(r"stumm|mute|aus\b", text, re.I):
                    neu = gear.audio_setzen(kanal, stumm=True)
                else:
                    neu = gear.stumm_umschalten(kanal)
                return self._fertig(f"{absicht}:{kanal}",
                                    f"{neu['label']} ist {'stumm' if neu['stumm'] else 'wieder an'}.")

            if absicht == "maus_sensi":
                if zahl is None:
                    return self._fehler("Auf welchen Wert soll ich die Sensi stellen?", "wert_unklar")
                r = gear.maus_dpi(zahl)
                return self._fertig(f"{absicht}:{r['dpi']}", f"Sensi auf {r['dpi']} DPI.")
        except gear.GearError as e:
            return self._fehler(f"Das ging nicht: {e}", f"{absicht}_fehler")
        return self._fehler("Das kann ich noch nicht.", "unbekannt")

    def spotify_befehl(self, absicht, text, a, playlists):
        if not self.spotify:
            if absicht == "spotify_abspielen":
                # ohne Spotify-Zugang wenigstens die Suche in der App öffnen
                return self.such_befehl(f"such in spotify nach {spotify_steuerung.suchtext(text)}",
                                        {"such_ort": type("Wahl", (), {"choice": "spotify", "confidence": 1.0})})
            return self._fehler("Spotify ist noch nicht eingerichtet.", "spotify_fehlt")

        if absicht == "spotify_was_laeuft":
            song = self.spotify.aktueller_song()
            if not song:
                return self._fertig(absicht, "Gerade läuft nichts.")
            return self._fertig(absicht, spotify_steuerung.beschreibe(song, "song").replace("Song ", "Das ist "))

        if absicht == "spotify_liken":
            if self.trocken:
                return self._fertig(absicht)
            song = self.spotify.like()
            if not song:
                return self._fehler("Gerade läuft kein Song.", "kein_song")
            return self._fertig(absicht, f"{song['name']} ist jetzt in deinen Lieblingssongs.")

        if absicht == "spotify_shuffle":
            an = a["shuffle_an"].noul >= 0.5
            if not self.trocken:
                self.spotify.shuffle(an)
            return self._fertig(f"shuffle:{'an' if an else 'aus'}", f"Shuffle {'an' if an else 'aus'}.")

        # spotify_abspielen
        art = a["spotify_art"].choice
        if art == "lieblingssongs":
            if not self.trocken:
                self.spotify.spiele_lieblingssongs()
            return self._fertig("spotify:lieblingssongs", "Ich spiele deine Lieblingssongs.")

        wahl = a.get("playlist")
        if art == "eigene_playlist" and wahl and wahl.choice != "keine" and wahl.confidence >= CONFIG["schwellen"]["ziel"]:
            name = playlists[int(wahl.choice[1:])]
            if not self.trocken:
                self.spotify.spiele_uri(self.spotify._playlists[name])
            return self._fertig(f"spotify:playlist:{name}", f"Ich spiele {name}.")

        such_art = {"eigene_playlist": "playlist", "playlist_suche": "playlist"}.get(art, art)
        suche = spotify_steuerung.suchtext(text)
        log.info("Spotify-Suche (%s): %s", such_art, suche)
        treffer = self.spotify.suche(suche, such_art)
        eintrag = self.treffer_waehlen(text, treffer, such_art) if treffer else None
        if not eintrag:
            return self._fehler("Dazu habe ich auf Spotify nichts gefunden.", "nicht_gefunden")
        beschreibung = spotify_steuerung.beschreibe(eintrag, such_art)
        if not self.trocken:
            self.spotify.spiele(eintrag, such_art)
        return self._fertig(f"spotify:{beschreibung}", f"Ich spiele {beschreibung}.")

    def discord_befehl(self, absicht, text, a):
        if absicht == "discord_mikro":
            if not self.trocken:
                self.discord.mikro()
            return self._fertig(absicht)

        if absicht == "discord_taub":
            if not self.trocken:
                self.discord.taub()
            return self._fertig(absicht)

        if absicht == "discord_neuigkeiten":
            neu = self.benachrichtigungen.abholen()
            if not neu:
                return self._fertig(absicht, "Keine neuen Discord-Nachrichten.")
            self.sprecher.sage(f"{len(neu)} neue Nachricht{'en' if len(neu) > 1 else ''}.")
            for n in neu[-10:]:
                self.sprecher.sage(f"{n['von']}: {n['text']}")
            return self._fertig(f"{absicht}:{len(neu)}")

        ziel_art = a["discord_ziel"].choice
        if absicht == "discord_oeffnen":
            name = discord_steuerung.ziel_name(text)
            if not name:
                return self._fehler("Was soll ich in Discord öffnen?", "ziel_unklar")
            if not self.trocken:
                self.discord.springe(ziel_art, name)
            return self._fertig(f"discord_oeffnen:{ziel_art}:{name}")

        # discord_nachricht
        if ziel_art not in ("kanal", "person"):
            ziel_art = "person"
        empfaenger, inhalt = discord_steuerung.nachricht_zerlegen(text)
        if not empfaenger or not inhalt:
            return self._fehler("Wem soll ich was schreiben?", "nachricht_unklar")
        if self.trocken:
            return self._fertig(f"discord_nachricht:{ziel_art}:{empfaenger}:{inhalt}")
        self.discord.springe(ziel_art, empfaenger)
        self.discord.tippe(inhalt)
        self.sprecher.sage(f"Nachricht an {empfaenger}: {inhalt}. Senden?")
        wartezeit = CONFIG["wartezeit_bestaetigung_sekunden"] + len(inhalt) / 12
        self.bestaetigung = {"bis": time.monotonic() + wartezeit}
        threading.Timer(wartezeit, self._bestaetigung_abgelaufen, args=[self.bestaetigung]).start()
        return f"discord_nachricht:{ziel_art}:{empfaenger}:{inhalt}"

    def _bestaetigung_beantworten(self, woerter):
        if woerter & JA_WOERTER and not woerter & NEIN_WOERTER:
            self._bestaetigung_beenden(senden=True)
        elif woerter & NEIN_WOERTER:
            self._bestaetigung_beenden(senden=False)
            self.sprecher.sage("Abgebrochen.")

    def _bestaetigung_beenden(self, senden):
        self.bestaetigung = None
        if not senden:
            self.discord.verwerfen()
        elif self.discord.senden():
            ton("ok")
            log.info("Discord-Nachricht gesendet")
        else:
            self._fehler("Discord ist nicht mehr im Vordergrund, ich habe nichts gesendet.", "nicht_gesendet")

    def _bestaetigung_abgelaufen(self, bestaetigung):
        if self.bestaetigung is bestaetigung:
            self._bestaetigung_beenden(senden=False)
            self.sprecher.sage("Keine Antwort, ich habe die Nachricht verworfen.")

    def timer_abgelaufen(self):
        ton("alarm")
        self.sprecher.sage("Dein Timer ist abgelaufen.")


def prozess_laeuft(name):
    ergebnis = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"], capture_output=True, text=True)
    return name.lower() in ergebnis.stdout.lower()


def erkenner(rate):
    import vosk

    vosk.SetLogLevel(-1)
    rec = vosk.KaldiRecognizer(vosk.Model(str(MODELL)), rate, json.dumps(wortschatz(), ensure_ascii=False))
    rec.SetWords(True)
    return rec


def verarbeite_audio(assistent, bloecke, rate):
    rec = erkenner(rate)
    puffer = Audiopuffer(rate)
    for block in bloecke:
        puffer.dazu(block)
        if rec.AcceptWaveform(block):
            assistent.gehoert(json.loads(rec.Result()), puffer)
    assistent.gehoert(json.loads(rec.FinalResult()), puffer)


def aus_wav(assistent, pfad):
    with wave.open(pfad) as w:
        bloecke = iter(lambda: w.readframes(4000), b"")
        verarbeite_audio(assistent, bloecke, w.getframerate())


def vom_mikrofon(assistent):
    import sounddevice as sd

    while True:
        try:
            geraet = sd.query_devices(kind="input")
            try:
                # 16 kHz direkt vom Treiber: sauberer als selbst umzurechnen
                sd.check_input_settings(samplerate=16000, channels=1, dtype="int16")
                rate = 16000
            except Exception:
                rate = int(geraet["default_samplerate"])
            puffer = queue.Queue()

            def callback(daten, frames, zeit, status):
                # Eigene Ansagen nicht mithören
                if not assistent.sprecher.spricht.is_set():
                    puffer.put(bytes(daten))

            with sd.RawInputStream(samplerate=rate, blocksize=rate // 4, dtype="int16", channels=1, callback=callback):
                log.info("Höre zu (Mikrofon: %s)", geraet["name"])
                verarbeite_audio(assistent, iter(puffer.get, None), rate)
        except Exception:
            log.exception("Mikrofon-Fehler, neuer Versuch in 5 Sekunden")
            time.sleep(5)
            sd._terminate()
            sd._initialize()


def logging_einrichten(konsole):
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    datei = RotatingFileHandler(BASIS / "jev-assistent.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    datei.setFormatter(fmt)
    log.addHandler(datei)
    if konsole and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
        k = logging.StreamHandler(sys.stdout)
        k.setFormatter(fmt)
        log.addHandler(k)


def laufende_pid():
    try:
        pid = int(PID_DATEI.read_text())
    except (OSError, ValueError):
        return None
    # tasklist antwortet in der Konsolen-Codepage; ohne errors="replace" wirft das Dekodieren
    # bei Sonderzeichen in einem Prozessnamen und der Assistent startet gar nicht erst.
    ergebnis = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                              capture_output=True, text=True, errors="replace")
    return pid if str(pid) in (ergebnis.stdout or "") else None


def main():
    p = argparse.ArgumentParser(description="Jev-Assistent")
    p.add_argument("--befehl", help="einen Befehl direkt an Jev schicken (ohne Weckwort)")
    p.add_argument("--wav", help="Audiodatei statt Mikrofon verwenden")
    p.add_argument("--trocken", action="store_true", help="nichts ausführen, nur protokollieren")
    p.add_argument("--still", action="store_true", help="keine Sprachausgabe")
    p.add_argument("--spotify-login", action="store_true", help="einmalig bei Spotify anmelden")
    p.add_argument("--stop", action="store_true", help="laufende Hintergrund-Instanz beenden")
    p.add_argument("--status", action="store_true", help="zeigen, ob der Assistent läuft")
    args = p.parse_args()

    if args.stop or args.status:
        pid = laufende_pid()
        if args.stop and pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            PID_DATEI.unlink(missing_ok=True)
            print("Jev-Assistent beendet.")
        else:
            print(f"Jev-Assistent läuft (PID {pid})." if pid else "Jev-Assistent läuft nicht.")
        return

    if args.spotify_login:
        if not CONFIG["spotify"]["client_id"]:
            print("Erst die Client ID in config.json unter spotify.client_id eintragen.")
            return
        sp = spotify_steuerung.Spotify(CONFIG["spotify"]["client_id"], SPOTIFY_TOKEN, "")
        print(f"Angemeldet als {sp.anmelden()}. {len(sp.playlists())} Playlists gefunden.")
        return

    logging_einrichten(konsole=sys.stdout is not None)
    assistent = Assistent(trocken=args.trocken, sprachausgabe=not args.still, mit_whisper=not args.befehl)

    if args.befehl:
        time.sleep(1.5)  # Playlists im Hintergrund laden lassen
        print(assistent.befehl(args.befehl))
        time.sleep(0.5)
        return
    if args.wav:
        aus_wav(assistent, args.wav)
        return

    if pid := laufende_pid():
        log.error("Läuft bereits (PID %s). Erst mit --stop beenden.", pid)
        return
    PID_DATEI.write_text(str(os.getpid()))
    try:
        vom_mikrofon(assistent)
    finally:
        PID_DATEI.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
