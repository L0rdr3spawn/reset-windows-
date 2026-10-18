"""tests.py - prüft Jeffs Textlogik ohne Mikrofon, Netz oder Tastendrücke.

  python tests.py
"""
import sys

import discord_steuerung as d
import jev_assistent as j

FAELLE = []


def fall(funktion):
    FAELLE.append(funktion)
    return funktion


def gleich(ist, soll):
    assert ist == soll, f"\n    ist:  {ist!r}\n    soll: {soll!r}"


@fall
def abbruchwoerter():
    for text in ["Nichts.", "nichts", "Vergiss es!", "egal", "schon gut", "Abbrechen.", "never mind"]:
        assert j.ABBRUCH.match(text), text
    for text in ["nichts mehr lauter", "stopp", "timer abbrechen", "spiel nichts von apache"]:
        assert not j.ABBRUCH.match(text), text


@fall
def mehrere_befehle():
    gleich(j.befehle_zerlegen("Öffne YouTube und suche nach TryMakes."), ["such auf youtube nach TryMakes"])
    gleich(j.befehle_zerlegen("öffne discord und such nach max"), ["öffne discord", "such in discord nach max"])
    gleich(j.befehle_zerlegen("starte spotify und dann spiel musik"), ["starte spotify", "spiel musik"])
    gleich(j.befehle_zerlegen("mach lauter und nächstes lied"), ["mach lauter", "nächstes lied"])
    # "und" ohne zweites Verb, im Suchbegriff oder im Diktat bleibt zusammen
    gleich(j.befehle_zerlegen("such nach tom und jerry"), ["such nach tom und jerry"])
    gleich(j.befehle_zerlegen("schreib max bin gleich da und mach schon mal auf"),
           ["schreib max bin gleich da und mach schon mal auf"])
    # "mach lauter" ist kein Ort: die Suche bleibt eigenständig
    gleich(j.befehle_zerlegen("mach lauter und such nach katzen"), ["mach lauter", "such nach katzen"])


@fall
def weckwort_sicherheit():
    def w(wort, conf, t=0.0):
        return {"word": wort, "conf": conf, "start": t, "end": t + 0.3}
    gleich(j.Assistent._weckwort_ende([w("hey", 1.0), w("jeff", 1.0), w("lauter", 1.0)]), 1)
    gleich(j.Assistent._weckwort_ende([w("okay", 1.0), w("hey", 0.59), w("jeff", 0.59)]), None)   # "hey chef"
    gleich(j.Assistent._weckwort_ende([w("hey", 1.0), w("heute", 1.0)]), None)


@fall
def suchbegriffe():
    gleich(j.suchbegriff("Such auf YouTube nach Minecraft Tutorials."), "Minecraft Tutorials")
    gleich(j.suchbegriff("Suche auf Amazon nach einer Gaming Maus"), "Gaming Maus")
    gleich(j.suchbegriff("such hier nach preis"), "preis")
    gleich(j.suchbegriff("google pizza in der nähe"), "pizza in der nähe")


@fall
def timer():
    gleich(j.dauer_sekunden("stell einen timer auf fünf minuten"), 300)
    gleich(j.dauer_sekunden("timer 90 sekunden"), 90)
    gleich(j.dauer_sekunden("halbe stunde"), 1800)
    gleich(j.dauer_sekunden("timer abbrechen"), None)
    gleich(j.rest_text(200), "3 Minuten 20 Sekunden")
    gleich(j.rest_text(45), "45 Sekunden")
    gleich(j.rest_text(60), "1 Minute")


@fall
def tasten():
    gleich(j.tasten_aus_text("drück strg z"), "ctrl+z")
    gleich(j.tasten_aus_text("alt tab"), "alt+tab")
    gleich(j.tasten_aus_text("drück enter"), "enter")


@fall
def discord_nachrichten():
    gleich(d.nachricht_zerlegen("Schreib Max, bin in fünf Minuten da."), ("Max", "bin in fünf Minuten da"))
    gleich(d.nachricht_zerlegen("schreib max bin gleich da"), ("max", "bin gleich da"))
    gleich(d.nachricht_zerlegen("schreib an max bin gleich da"), ("max", "bin gleich da"))
    gleich(d.nachricht_zerlegen("Schreib an Max, bin gleich da"), ("Max", "bin gleich da"))


@fall
def spiele_erkennung():
    import fenster
    alt = fenster.pfad
    try:
        fenster.pfad = lambda hwnd: r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"
        assert j.ist_spiel({"hwnd": 0, "prozess": "cs2.exe"})
        fenster.pfad = lambda hwnd: r"C:\Program Files\Epic Games\Fortnite\FortniteClient-Win64-Shipping.exe"
        assert j.ist_spiel({"hwnd": 0, "prozess": "FortniteClient-Win64-Shipping.exe"})
        fenster.pfad = lambda hwnd: r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        assert not j.ist_spiel({"hwnd": 0, "prozess": "chrome.exe"})
    finally:
        fenster.pfad = alt


@fall
def prozess_nicht_da_ohne_absturz():
    # tasklist-Meldung "keine Aufgaben ... ausgeführt" enthält ein OEM-"ü" - stürzte früher ab
    gleich(j.prozess_laeuft("gibt_es_nicht_123.exe"), False)


class _Wahl:
    def __init__(self, choice, confidence=1.0):
        self.choice, self.confidence = choice, confidence


def _assistent_ohne_netz():
    a = j.Assistent.__new__(j.Assistent)
    a.trocken, a._fehlgeschlagen, a.timer = False, False, []
    a.sprecher = j.Sprecher(False)
    return a


@fall
def hier_sucht_im_aktiven_fenster():
    a = _assistent_ohne_netz()
    a.trocken = True
    import fenster
    alt = fenster.aktives, fenster.pfad
    try:
        fenster.aktives = lambda: {"hwnd": 1, "titel": "Rezept - Brave", "prozess": "brave.exe"}
        fenster.pfad = lambda hwnd: r"C:\Users\x\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"
        # Jev meinte "youtube" - "hier" muss trotzdem die offene Seite durchsuchen
        ergebnis = a.such_befehl("such hier nach youtube", {"such_ort": _Wahl("youtube")})
        gleich(ergebnis, "suchen:brave.exe:ctrl+f:youtube")
    finally:
        fenster.aktives, fenster.pfad = alt


@fall
def kein_tippen_nach_fokusverlust():
    import fenster
    import tastatur
    a = _assistent_ohne_netz()
    getippt = []
    alt = fenster.aktives, fenster.pfad, fenster.ist_vorne, tastatur.einfuegen, tastatur.druecke
    try:
        fenster.aktives = lambda: {"hwnd": 1, "titel": "Rezept - Brave", "prozess": "brave.exe"}
        fenster.pfad = lambda hwnd: r"C:\Programme\brave.exe"
        fenster.ist_vorne = lambda hwnd: False          # jemand hat Discord angeklickt
        tastatur.einfuegen = lambda text: getippt.append(text)
        tastatur.druecke = lambda kombi, anzahl=1: getippt.append(kombi)
        gleich(a.fenster_befehl("text_schreiben", "tippe hallo zusammen", {}), "fokus_verloren")
        gleich(a.such_befehl("such hier nach preis", {"such_ort": _Wahl("programm")}), "fokus_verloren")
        gleich(getippt, [])
    finally:
        fenster.aktives, fenster.pfad, fenster.ist_vorne, tastatur.einfuegen, tastatur.druecke = alt


@fall
def chat_programme_ohne_enter():
    gleich(j.CONFIG["apps"]["discord"].get("chat"), True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    fehler = 0
    for f in FAELLE:
        try:
            f()
            print(f"  ok    {f.__name__}")
        except AssertionError as e:
            fehler += 1
            print(f"  FEHLER {f.__name__}: {e}")
    print(f"\n{len(FAELLE) - fehler}/{len(FAELLE)} bestanden")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
