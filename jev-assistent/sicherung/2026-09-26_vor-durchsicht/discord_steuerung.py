"""Discord-Steuerung über Tastenkürzel und den Quick Switcher, plus Benachrichtigungen.

Discord hat keine offizielle Schnittstelle, um den eigenen Client zu steuern.
Deshalb bedient das Programm Discord so, wie du es mit der Tastatur tun würdest.
"""

import logging
import os
import re
import sqlite3
import threading
import time
from contextlib import closing
import xml.etree.ElementTree as ET

import tastatur

log = logging.getLogger("jev")

# Präfixe des Quick Switchers (Strg+K)
PRAEFIX = {"kanal": "#", "sprachkanal": "!", "person": "@", "server": "*"}

_ZIEL_ANFANG = re.compile(
    r"^(bitte\s+)?(öffne|öffnen|geh|gehe|wechsel|wechsle|spring|springe|join|joine|tritt|betrete|zeig|zeige|schreib|schreibe|schick|schicke|sende|sag|sage)?\s*"
    r"(mir\s+)?(in\s+|zu\s+|zum\s+|zur\s+|auf\s+|an\s+|bei\s+)?(den\s+|die\s+|das\s+|dem\s+|der\s+|meinen\s+|meine\s+|unseren\s+|unser\s+)?"
    r"((sprachkanal|sprach-kanal|voice-?kanal|kanal|channel|server|chat|dm)\s+)?(mit\s+|von\s+)?",
    re.IGNORECASE)
_ZIEL_ENDE = re.compile(
    r"(\s*\b(sprachkanal|sprach-kanal|voice-?kanal|voice|kanal|channel|server|chat|dm|bei|beitreten|auf\s+discord|in\s+discord|discord)\b)*\s*$",
    re.IGNORECASE)


def ziel_name(text):
    """ "öffne den Gaming-Kanal" -> "Gaming" """
    text = re.sub(r"[.!?]", " ", text).strip()
    text = _ZIEL_ENDE.sub("", _ZIEL_ANFANG.sub("", text, count=1)).strip(" -")
    return text


def nachricht_zerlegen(text):
    """ "Schreib Max, bin in fünf Minuten da." -> ("Max", "bin in fünf Minuten da") """
    treffer = re.match(r"^\W*(?P<kopf>.+?)\s*[,:!;]\s*(?P<text>.+)$", text.strip())
    if treffer:
        kopf, inhalt = treffer["kopf"], treffer["text"]
    else:
        # Ohne Satzzeichen: das erste Wort nach dem Verb ist der Empfänger
        teile = text.split()
        kopf, inhalt = " ".join(teile[:2]), " ".join(teile[2:])
    inhalt = inhalt.strip().rstrip(".!")
    return ziel_name(kopf), inhalt


class Discord:
    def __init__(self, konfig, start_befehl):
        self.tasten = konfig["tasten"]
        self.namen = {k.lower(): v for k, v in konfig.get("namen", {}).items()}
        self.start_befehl = start_befehl

    def mikro(self):
        tastatur.druecke(self.tasten["mikro"])

    def taub(self):
        tastatur.druecke(self.tasten["taub"])

    def ist_vorne(self):
        return tastatur.vordergrund_prozess().lower() == "discord.exe"

    def nach_vorne(self):
        """Ein zweiter Discord-Start holt das laufende Fenster nach vorne."""
        if self.ist_vorne():
            return True
        os.startfile(os.path.expandvars(self.start_befehl["start"]), arguments=self.start_befehl.get("argumente", ""))
        for _ in range(50):
            time.sleep(0.2)
            if self.ist_vorne():
                time.sleep(0.5)
                return True
        return False

    def suchname(self, name):
        return self.namen.get(name.lower(), name)

    def springe(self, art, name):
        """Öffnet Kanal, Person oder Server über den Quick Switcher."""
        if not self.nach_vorne():
            raise RuntimeError("Discord-Fenster ließ sich nicht öffnen")
        tastatur.druecke("ctrl+k")
        time.sleep(0.5)
        tastatur.tippe(PRAEFIX.get(art, "") + self.suchname(name))
        time.sleep(1.2)
        tastatur.druecke("enter")
        time.sleep(1.0)

    def tippe(self, text):
        tastatur.tippe(text)

    def senden(self):
        if not self.ist_vorne():
            return False
        tastatur.druecke("enter")
        return True

    def verwerfen(self):
        if self.ist_vorne():
            tastatur.druecke("ctrl+a")
            tastatur.druecke("backspace")


class Benachrichtigungen(threading.Thread):
    """Liest neue Discord-Benachrichtigungen aus dem Windows-Benachrichtigungscenter."""

    DB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db")

    def __init__(self):
        super().__init__(daemon=True)
        self.neu = []
        self.gesehen = 0
        self.sperre = threading.Lock()

    def run(self):
        while True:
            try:
                self._abfragen()
            except Exception as e:
                log.debug("Benachrichtigungen nicht lesbar: %s", e)
            time.sleep(2)

    def _abfragen(self):
        with closing(sqlite3.connect(f"file:{self.DB}?mode=ro", uri=True, timeout=1)) as db:
            zeilen = db.execute(
                "SELECT n.Id, n.Payload FROM Notification n JOIN NotificationHandler h ON n.HandlerId = h.RecordId "
                "WHERE h.PrimaryId LIKE '%Discord%' AND n.Id > ? ORDER BY n.Id", (self.gesehen,)).fetchall()
        for nid, payload in zeilen:
            self.gesehen = max(self.gesehen, nid)
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", "replace")
            texte = [t.text.strip() for t in ET.fromstring(payload).iter("text") if t.text and t.text.strip()]
            if texte:
                with self.sperre:
                    self.neu.append({"von": texte[0], "text": " ".join(texte[1:])})
                    del self.neu[:-50]
                log.info("Discord-Benachrichtigung von %s", texte[0])

    def abholen(self):
        with self.sperre:
            neu, self.neu = self.neu, []
        return neu
