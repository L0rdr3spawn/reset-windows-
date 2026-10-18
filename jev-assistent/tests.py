"""tests.py - prüft Jeffs Textlogik ohne Mikrofon, Netz oder Tastendrücke.

  python tests.py
"""
import sys

import aktivierung
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
def weckwort_reste():
    jeff = {"name": "Jeff", "weckwort": "hey jeff"}
    gleich(aktivierung.weckwort_entfernen("Hey Jeff, wie spät ist es?", jeff), "wie spät ist es?")
    gleich(aktivierung.weckwort_entfernen("Yif! Spiel was von Apache", jeff), "Spiel was von Apache")
    gleich(aktivierung.weckwort_entfernen("hey jeff, such nach x", {}), "such nach x")      # alte Config ohne "name"
    kevin = {"name": "Kevin", "weckwort": "hey kevin"}
    gleich(aktivierung.weckwort_entfernen("hey kevin wie spät ist es", kevin), "wie spät ist es")
    gleich(aktivierung.weckwort_entfernen("Kevin, öffne Spotify.", kevin), "öffne Spotify.")
    # Jeffs Verhörer gelten nur, solange er Jeff heißt
    gleich(aktivierung.weckwort_entfernen("Yif! Spiel was", kevin), "Yif! Spiel was")
    gleich(aktivierung.weckwort_entfernen("hey, wie spät ist es", kevin), "hey, wie spät ist es")
    gleich(aktivierung.weckwort_entfernen("Computer: öffne Discord", {"name": "Kevin", "weckwort": "Computer"}),
           "öffne Discord")
    gleich(aktivierung.weckwort({"name": "Kevin"}), "hey kevin")          # ohne Weckwort: "hey <name>"
    gleich(aktivierung.weckwort({"weckwort": "Hey, Kevin!"}), "hey kevin")
    gleich(aktivierung.name({}), "Jeff")


@fall
def weckwort_mit_anderem_namen():
    def w(wort, conf=1.0, t=0.0):
        return {"word": wort, "conf": conf, "start": t, "end": t + 0.3}
    alt = dict(j.CONFIG)
    try:
        j.CONFIG.update(name="Kevin", weckwort="hey kevin")
        gleich(j.Assistent._weckwort_ende([w("hey"), w("kevin"), w("lauter")]), 1)
        gleich(j.Assistent._weckwort_ende([w("hey"), w("jeff"), w("lauter")]), None)
        gleich(j.wortschatz()[0], "hey kevin")
        gleich(j.suchbegriff("Hey Kevin, such auf YouTube nach Katzen"), "Katzen")
    finally:
        j.CONFIG.clear()
        j.CONFIG.update(alt)
    gleich(j.suchbegriff("Hey Jeff, such auf YouTube nach Katzen"), "Katzen")


@fall
def weckwort_wortschatz():
    # Vosk lässt unbekannte Wörter stillschweigend aus der Grammatik fallen
    gleich(aktivierung.unbekannte_woerter("hey jeff"), [])
    gleich(aktivierung.unbekannte_woerter("Hey Kevin"), [])
    gleich(aktivierung.unbekannte_woerter("hey jev"), ["jev"])
    gleich(aktivierung.unbekannte_woerter("okay xyzqq"), ["xyzqq"])


@fall
def tastenkuerzel():
    gleich(aktivierung.tastenkuerzel_lesen("ctrl+alt+j"), (aktivierung.MOD_CONTROL | aktivierung.MOD_ALT, 0x4A))
    gleich(aktivierung.tastenkuerzel_lesen("ctrl+shift+f8"), (aktivierung.MOD_CONTROL | aktivierung.MOD_SHIFT, 0x77))
    gleich(aktivierung.tastenkuerzel_lesen("alt+space"), (aktivierung.MOD_ALT, 0x20))
    gleich(aktivierung.tastenkuerzel_lesen("Strg + Umschalt + 5"), (aktivierung.MOD_CONTROL | aktivierung.MOD_SHIFT, 0x35))
    gleich(aktivierung.tastenkuerzel_lesen("win+alt+k"), (aktivierung.MOD_WIN | aktivierung.MOD_ALT, 0x4B))
    gleich(aktivierung.tastenkuerzel_normal("Alt+Strg+J"), "ctrl+alt+j")
    gleich(aktivierung.tastenkuerzel_anzeige("ctrl+alt+j"), "Strg+Alt+J")
    gleich(aktivierung.tastenkuerzel_anzeige("ctrl+shift+f8"), "Strg+Umschalt+F8")
    gleich(aktivierung.tastenkuerzel_anzeige(""), "")
    gleich(aktivierung.taste_von_vk(0x4A), "j")
    for kaputt in ["", "ctrl+alt", "ctrl+xyz", "ctrl+a+b"]:
        try:
            aktivierung.tastenkuerzel_lesen(kaputt)
            raise AssertionError(f"{kaputt!r} hätte abgelehnt werden müssen")
        except ValueError:
            pass
    gleich(aktivierung.tastenkuerzel_pruefen("ctrl+alt+j"), None)
    gleich(aktivierung.tastenkuerzel_pruefen("f8"), None)
    assert aktivierung.tastenkuerzel_pruefen("j"), "einzelner Buchstabe würde beim Tippen auslösen"
    assert aktivierung.tastenkuerzel_pruefen("shift+j"), "Umschalt+Buchstabe ist ein Großbuchstabe"


@fall
def tastenkuerzel_weckt():
    """Tastenkürzel -> wie Weckwort ohne Befehl; der nächste Satz wird ab dem Tastendruck verarbeitet."""
    a = _assistent_ohne_netz()
    gehoert = []
    a.befehl_aus_audio = lambda puffer, von, bis, text: gehoert.append((von, bis, text))

    class Rec:
        zurueckgesetzt = False

        def Reset(self):
            Rec.zurueckgesetzt = True

    puffer = j.Audiopuffer(16000)
    puffer.dazu(b"\0\0" * 16000 * 3)                 # 3 s Audio vor dem Tastendruck
    alt_ton, j.ton = j.ton, lambda art: None
    try:
        a.per_taste_wecken(Rec(), puffer)
    finally:
        j.ton = alt_ton
    assert Rec.zurueckgesetzt and a.wartet_bis, "Tastenkürzel muss zuhören lassen"
    gleich(a.befehl_ab, 3.0)
    a.gehoert({"result": [{"word": "wie", "start": 2.5, "end": 3.4, "conf": 1.0},
                          {"word": "spät", "start": 3.4, "end": 3.8, "conf": 1.0}]}, puffer)
    gleich(gehoert, [(3.0, 3.8, "wie spät")])


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
    a.rueckfrage, a.gespraech, a.hoeren_ab, a._nutzer_text = None, [], 0.0, ""
    a.wartet_bis, a.befehl_ab, a.bestaetigung, a.spotify = None, 0.0, None, None
    return a


def _woerter(*paare):
    return {"result": [{"word": w, "start": s, "end": s + 0.4, "conf": 1.0} for w, s in paare]}


@fall
def rueckfrage_hoert_ohne_weckwort():
    """'Welches Programm meinst du?' -> die Antwort danach braucht kein "hey jeff"."""
    a = _assistent_ohne_netz()
    a.trocken = True
    a._nutzer_text = "öffne seelen ui"
    a._fehler("Welches Programm meinst du?", "ziel_unklar")
    assert a.rueckfrage, "Rückfrage muss offen sein"
    gleich(a.gespraech, [{"wer": "person", "text": "öffne seelen ui"},
                         {"wer": "assistent", "text": "Welches Programm meinst du?"}])
    gehoert = []
    a.befehl_aus_audio = lambda puffer, von, bis, text, rueckfrage=False: gehoert.append((von, text, rueckfrage))
    puffer = j.Audiopuffer(16000)
    puffer.dazu(b"\0\0" * 16000 * 3)
    a.gehoert(_woerter(("visual", 2.0), ("code", 2.4)), puffer)
    gleich(gehoert, [(2.0, "visual code", True)])
    # mit Weckwort davor zählt es genauso als Antwort, ohne das Weckwort
    gehoert.clear()
    a.gehoert(_woerter(("hey", 1.0), ("jeff", 1.3), ("visual", 2.0)), puffer)
    gleich(gehoert, [(2.0, "visual", True)])


@fall
def rueckfrage_verfaellt():
    a = _assistent_ohne_netz()
    a.trocken = True
    a._fehler("Wonach soll ich suchen?", "begriff_unklar")
    a.rueckfrage["seit"] = a.sprecher.fertig_um = j.time.monotonic() - 60
    gehoert = []
    a.befehl_aus_audio = lambda *x, **k: gehoert.append(x)
    puffer = j.Audiopuffer(16000)
    puffer.dazu(b"\0\0" * 16000 * 3)
    a.gehoert(_woerter(("katzen", 2.0)), puffer)
    gleich(gehoert, [])
    assert a.rueckfrage is None and a.gespraech == []


@fall
def keine_rueckfrage_ohne_fragezeichen():
    a = _assistent_ohne_netz()
    a.trocken = True
    a._fertig("uhrzeit", "Es ist 16 Uhr.")
    assert a.rueckfrage is None


@fall
def rueckfrage_antwort_mit_verlauf():
    """Die Antwort geht mit dem bisherigen Gespräch an Claude, der daraus den ganzen Befehl macht."""
    import fenster
    a = _assistent_ohne_netz()
    a.trocken = True
    a._nutzer_text = "öffne seelen ui"
    a._fehler("Welches Programm meinst du?", "ziel_unklar")
    gefragt, ausgefuehrt = [], []

    def frage(text, absichten, alternativ=None, kontext=None):
        gefragt.append((text, kontext["verlauf"][:]))
        return {"art": "befehl", "befehl": "öffne visual studio code", "antwort": ""}

    a.befehl = lambda text, alternativ=None, von_claude=False: ausgefuehrt.append(text) or "app_oeffnen:vs_code"
    alt = j.claude.frage, j.ton, fenster.aktives, fenster.liste, j.CONFIG["claude"]["aktiv"]
    try:
        j.claude.frage, j.ton = frage, lambda art: None
        fenster.aktives, fenster.liste = lambda: {"titel": "Desktop"}, lambda: []
        j.CONFIG["claude"]["aktiv"] = True
        gleich(a.rueckfrage_beantworten("visual studio code"), "app_oeffnen:vs_code")
    finally:
        j.claude.frage, j.ton, fenster.aktives, fenster.liste, j.CONFIG["claude"]["aktiv"] = alt
    gleich(gefragt, [("visual studio code", [{"wer": "person", "text": "öffne seelen ui"},
                                             {"wer": "assistent", "text": "Welches Programm meinst du?"}])])
    gleich(ausgefuehrt, ["öffne visual studio code"])
    assert a.rueckfrage is None and a.gespraech == [], "nach erledigtem Befehl ist das Gespräch zu Ende"


@fall
def gegenfrage_im_gespraech():
    """Claude fragt zurück ("Und dir?") -> Jeff hört weiter zu, der Verlauf wächst mit."""
    a = _assistent_ohne_netz()
    a.trocken = True
    a._nutzer_text = "wie geht's"
    a._fertig("claude_antwort", "Mir geht's gut, danke! Und dir?")
    assert a.rueckfrage
    a._nutzer_text = "auch gut"
    a._fertig("claude_antwort", "Schön! Was kann ich für dich tun?")
    gleich([t["text"] for t in a.gespraech],
           ["wie geht's", "Mir geht's gut, danke! Und dir?", "auch gut", "Schön! Was kann ich für dich tun?"])


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
