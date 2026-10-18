"""Spotify-Steuerung über die Web-API (Wiedergabe steuern braucht Premium)."""

import logging
import os
import re
import time

import spotipy
from spotipy.oauth2 import SpotifyPKCE

log = logging.getLogger("jev")

SCOPES = " ".join([
    "user-read-playback-state", "user-modify-playback-state", "user-read-currently-playing",
    "user-library-read", "user-library-modify", "playlist-read-private", "playlist-read-collaborative",
])
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SUCHTYP = {"song": "track", "kuenstler": "artist", "album": "album", "playlist": "playlist"}

# Füllwörter am Anfang und Ende, damit nur "apache 207" in die Suche geht
_ANFANG = re.compile(
    r"^(bitte\s+)?(spiel|spiele|spielt|abspielen|leg|lege|mach|mache|starte|hör|höre)?\s*(mal\s+|bitte\s+|mir\s+|uns\s+|meine\s+|meinen\s+|mein\s+)*"
    r"(was|etwas|musik|lieder|songs?|den\s+song|das\s+lied|ein\s+lied|einen\s+song|das\s+album|die\s+playlist|meine\s+playlist)?\s*"
    r"(von\s+|vom\s+|mit\s+)?", re.IGNORECASE)
_ENDE = re.compile(r"\s*(auf\s+spotify|ab|an|bitte|playlist)?\s*$", re.IGNORECASE)


def suchtext(befehl):
    text = re.sub(r"[.!?,]", " ", befehl).strip()
    text = _ENDE.sub("", _ANFANG.sub("", text, count=1)).strip()
    return text or befehl


def beschreibe(eintrag, art):
    kuenstler = ", ".join(a["name"] for a in eintrag.get("artists", []))
    if art == "song":
        return f"Song \"{eintrag['name']}\" von {kuenstler}"
    if art == "album":
        return f"Album \"{eintrag['name']}\" von {kuenstler}"
    if art == "playlist":
        return f"Playlist \"{eintrag['name']}\" von {eintrag.get('owner', {}).get('display_name', '?')}"
    return f"Künstler {eintrag['name']}"


class Spotify:
    def __init__(self, client_id, token_datei, spotify_exe):
        self.auth = SpotifyPKCE(
            client_id=client_id, redirect_uri=REDIRECT_URI, scope=SCOPES, open_browser=True,
            cache_handler=spotipy.CacheFileHandler(cache_path=str(token_datei)),
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth, requests_timeout=10, retries=2)
        self.spotify_exe = spotify_exe
        self._playlists = {}
        self._playlists_zeit = 0

    def angemeldet(self):
        return self.auth.cache_handler.get_cached_token() is not None

    def anmelden(self):
        """Öffnet beim ersten Mal den Browser zum Einloggen."""
        return self.sp.current_user()["display_name"]

    def playlists(self):
        """Eigene und gefolgte Playlists als {Name: URI}, 10 Minuten zwischengespeichert."""
        if time.time() - self._playlists_zeit > 600:
            gefunden = {}
            seite = self.sp.current_user_playlists(limit=50)
            while seite:
                for p in seite["items"]:
                    if p:
                        gefunden[p["name"]] = p["uri"]
                seite = self.sp.next(seite) if seite.get("next") else None
            self._playlists, self._playlists_zeit = gefunden, time.time()
        return self._playlists

    def geraet(self):
        """Aktives Gerät, sonst dieser PC; startet Spotify, falls es nicht läuft."""
        for versuch in range(20):
            geraete = self.sp.devices()["devices"]
            aktiv = next((g for g in geraete if g["is_active"]), None)
            if aktiv:
                return aktiv["id"]
            pc = next((g for g in geraete if g["type"] == "Computer"), None)
            if pc:
                return pc["id"]
            if versuch == 0:
                log.info("Kein Spotify-Gerät aktiv, starte Spotify")
                os.startfile(self.spotify_exe)
            time.sleep(1)
        raise RuntimeError("Kein Spotify-Gerät gefunden")

    def suche(self, text, art, anzahl=5):
        typ = SUCHTYP[art]
        treffer = self.sp.search(q=text, type=typ, limit=anzahl, market="from_token")[typ + "s"]["items"]
        return [t for t in treffer if t]

    def spiele(self, eintrag, art, shuffle=None):
        geraet = self.geraet()
        if shuffle is not None:
            self.sp.shuffle(shuffle, device_id=geraet)
        if art == "song":
            self.sp.start_playback(device_id=geraet, uris=[eintrag["uri"]])
        else:
            self.sp.start_playback(device_id=geraet, context_uri=eintrag["uri"])

    def spiele_uri(self, uri):
        self.sp.start_playback(device_id=self.geraet(), context_uri=uri)

    def spiele_lieblingssongs(self):
        songs = [t["track"]["uri"] for t in self.sp.current_user_saved_tracks(limit=50)["items"] if t.get("track")]
        geraet = self.geraet()
        self.sp.shuffle(True, device_id=geraet)
        self.sp.start_playback(device_id=geraet, uris=songs)

    def aktueller_song(self):
        jetzt = self.sp.current_playback()
        if not jetzt or not jetzt.get("item"):
            return None
        return jetzt["item"]

    def like(self):
        song = self.aktueller_song()
        if not song:
            return None
        self.sp.current_user_saved_tracks_add([song["id"]])
        return song

    def shuffle(self, an):
        self.sp.shuffle(an, device_id=self.geraet())
