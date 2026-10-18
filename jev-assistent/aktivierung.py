"""aktivierung.py - Name, Weckwort und Tastenkürzel des Assistenten.

Bewusst ohne schwere Abhängigkeiten (kein numpy, Vosk oder Whisper): die
Einstellungs-Oberfläche nutzt dieselben Funktionen wie jev_assistent.py.

  python aktivierung.py "hey kevin"      prüfen, ob die Weckwort-Erkennung die Wörter kennt
"""
import ctypes
import ctypes.wintypes as wt
import re
import struct
import threading
from pathlib import Path

BASIS = Path(__file__).resolve().parent
MODELL = BASIS / "vosk-model-small-de-0.15"
STANDARD_NAME = "Jeff"

# Begrüßungen vor dem Namen ("hey kevin", "okay kevin") - Whisper schreibt sie mal so, mal so
GRUESSE = ("hey", "hei", "hay", "he", "hallo", "hi", "ok", "okay", "yo", "servus", "moin")
# So hat Whisper "hey jeff" schon aufgeschrieben ("Yif! Spiel ...") - gilt nur, solange er Jeff heißt
JEFF_VARIANTEN = ("jev", "jeff", "jef", "yif", "yiff", "if", "jeb", "chef")


# --- Name und Weckwort --------------------------------------------------

def normal(text):
    """'Hey, Kevin!' -> 'hey kevin' (so stehen die Wörter im Vosk-Wortschatz)."""
    return " ".join(re.sub(r"[^\w\s'-]", " ", (text or "").lower()).split())


def name(cfg):
    """Name des Assistenten aus config.json; alte Configs ohne "name" heißen Jeff."""
    return " ".join(str(cfg.get("name") or "").split()) or STANDARD_NAME


def standard_weckwort(name_):
    return normal(f"hey {name_}")


def weckwort(cfg):
    """Aktivierungswort aus config.json; fehlt es, gilt "hey <name>"."""
    return normal(cfg.get("weckwort")) or standard_weckwort(name(cfg))


def namens_teil(weckwort_):
    """'hey kevin' -> 'kevin': das Weckwort ohne Begrüßung davor."""
    woerter = normal(weckwort_).split()
    i = 0
    while i < len(woerter) - 1 and woerter[i] in GRUESSE:
        i += 1
    return " ".join(woerter[i:])


_muster_cache = {}


def weckwort_muster(cfg):
    """Regex für Weckwort-Reste am Satzanfang, abgeleitet aus Name und Weckwort.

    Begrüßung ist optional, der Name nicht: "hey kevin, wie spät" und "Kevin, wie spät"
    verlieren den Anfang, "hey, wie spät" bleibt unverändert.
    """
    w, n = weckwort(cfg), normal(name(cfg))
    schluessel = (w, n)
    if schluessel not in _muster_cache:
        rest = namens_teil(w)
        gruesse = set(GRUESSE) | set(w.split()[:len(w.split()) - len(rest.split())])
        namen = {rest, n} - {""}
        if namen & {"jeff", "hey jeff"} or n == "jeff":
            namen |= set(JEFF_VARIANTEN)
        alternativen = "|".join(r"\W+".join(map(re.escape, x.split()))
                                for x in sorted(namen, key=len, reverse=True))
        gruss = "|".join(map(re.escape, sorted(gruesse, key=len, reverse=True)))
        _muster_cache[schluessel] = re.compile(rf"^\W*(({gruss})\W*)?({alternativen})\b\W*", re.I)
    return _muster_cache[schluessel]


def weckwort_entfernen(text, cfg):
    """'Hey Kevin, wie spät ist es?' -> 'wie spät ist es?'"""
    return weckwort_muster(cfg).sub("", text, count=1)


# --- Wortschatz der Weckwort-Erkennung ------------------------------------
# Vosk lässt Wörter, die sein Modell nicht kennt, in der Grammatik stillschweigend weg
# ("Ignoring word missing in vocabulary"). Aus "hey xyz" würde "hey" - und das Weckwort
# käme nie vollständig an. Das kleine deutsche Modell hat keine words.txt; die Wörter
# stehen als Symboltabelle im Kopf von graph/Gr.fst (OpenFST-Binärformat).

_FST_MAGIC, _SYMBOLE_MAGIC = 2125659606, 2125658996
_wortschatz = {}


def _symboltabelle(datei):
    def zahl32():
        return struct.unpack("<i", datei.read(4))[0]

    def zahl64():
        return struct.unpack("<q", datei.read(8))[0]

    def text():
        return datei.read(zahl32())

    if zahl32() != _FST_MAGIC:
        raise ValueError("keine OpenFST-Datei")
    text(), text()                       # FST-Typ, Bogen-Typ
    zahl32()                             # Version
    flags = zahl32()
    zahl64(), zahl64(), zahl64(), zahl64()   # Eigenschaften, Start, Zustände, Bögen
    if not flags & 3:
        raise ValueError("keine Symboltabelle in der FST")
    if zahl32() != _SYMBOLE_MAGIC:
        raise ValueError("Symboltabelle unlesbar")
    text()
    zahl64()
    anzahl = zahl64()
    woerter = set()
    for _ in range(anzahl):
        woerter.add(text().decode("utf-8", "replace"))
        zahl64()
    return woerter


def modell_woerter(modell=MODELL):
    """Alle Wörter, die das Vosk-Modell kennt. -> set | None (nicht lesbar)"""
    modell = Path(modell)
    if modell not in _wortschatz:
        woerter = None
        try:
            liste = modell / "graph" / "words.txt"          # große Modelle
            if liste.exists():
                woerter = {z.split()[0] for z in liste.read_text(encoding="utf-8").splitlines() if z.strip()}
            else:
                with open(modell / "graph" / "Gr.fst", "rb") as datei:
                    woerter = _symboltabelle(datei)
        except (OSError, ValueError, struct.error, IndexError):
            woerter = None
        _wortschatz[modell] = woerter
    return _wortschatz[modell]


def unbekannte_woerter(text, modell=MODELL):
    """Wörter aus `text`, die die Weckwort-Erkennung nicht kennt. -> list | None (Wortschatz unlesbar)"""
    bekannt = modell_woerter(modell)
    if bekannt is None:
        return None
    return [w for w in normal(text).split() if w not in bekannt]


# --- Tastenkürzel --------------------------------------------------------

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
ERROR_HOTKEY_ALREADY_REGISTERED = 1409

ZUSATZ = {"ctrl": MOD_CONTROL, "shift": MOD_SHIFT, "alt": MOD_ALT, "win": MOD_WIN}
ZUSATZ_ALIASE = {"strg": "ctrl", "control": "ctrl", "steuerung": "ctrl", "umschalt": "shift",
                 "windows": "win", "altgr": "alt"}

TASTEN = {
    "space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B, "backspace": 0x08,
    "delete": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28, "pause": 0x13, "print": 0x2C,
    "plus": 0xBB, "comma": 0xBC, "minus": 0xBD, "period": 0xBE,
    **{chr(c): c - 32 for c in range(ord("a"), ord("z") + 1)},      # VK_A = 0x41 ("A")
    **{str(z): 0x30 + z for z in range(10)},
    **{f"num{z}": 0x60 + z for z in range(10)},
    **{f"f{n}": 0x6F + n for n in range(1, 25)},
}
TASTEN_ALIASE = {"leertaste": "space", "leer": "space", "return": "enter", "eingabe": "enter",
                 "escape": "esc", "entf": "delete", "del": "delete", "einfg": "insert", "ins": "insert",
                 "pos1": "home", "ende": "end", "bildauf": "pageup", "pgup": "pageup", "bildab": "pagedown",
                 "pgdn": "pagedown", "rücktaste": "backspace", "links": "left", "rechts": "right",
                 "hoch": "up", "oben": "up", "runter": "down", "unten": "down", "druck": "print",
                 "komma": "comma", "punkt": "period"}
ANZEIGE = {"ctrl": "Strg", "shift": "Umschalt", "alt": "Alt", "win": "Win", "space": "Leertaste",
           "enter": "Enter", "tab": "Tab", "esc": "Esc", "backspace": "Rücktaste", "delete": "Entf",
           "insert": "Einfg", "home": "Pos1", "end": "Ende", "pageup": "Bild auf", "pagedown": "Bild ab",
           "left": "Links", "up": "Hoch", "right": "Rechts", "down": "Runter", "pause": "Pause",
           "print": "Druck", "plus": "+", "comma": "Komma", "minus": "-", "period": "Punkt"}
_VK_NAME = {vk: n for n, vk in TASTEN.items()}


def tastenkuerzel_teile(text):
    """'Strg + Alt + J' -> (['ctrl', 'alt'], 'j'); wirft ValueError mit deutscher Meldung."""
    roh = [t for t in re.sub(r"\s+", "", (text or "").lower()).split("+") if t]
    if (text or "").strip().endswith("++"):
        roh.append("plus")
    zusatz, taste = [], None
    for teil in roh:
        teil = ZUSATZ_ALIASE.get(teil, teil)
        if teil in ZUSATZ:
            if teil not in zusatz:
                zusatz.append(teil)
            continue
        teil = TASTEN_ALIASE.get(teil, teil)
        if teil not in TASTEN:
            raise ValueError(f"Unbekannte Taste: {teil}")
        if taste:
            raise ValueError("Nur eine Taste neben Strg, Alt, Umschalt und Win möglich")
        taste = teil
    if not taste:
        raise ValueError("Es fehlt die eigentliche Taste (z. B. Strg+Alt+J)")
    zusatz.sort(key=list(ZUSATZ).index)
    return zusatz, taste


def tastenkuerzel_lesen(text):
    """'ctrl+alt+j' -> (MOD_CONTROL | MOD_ALT, 0x4A) für RegisterHotKey."""
    zusatz, taste = tastenkuerzel_teile(text)
    mods = 0
    for z in zusatz:
        mods |= ZUSATZ[z]
    return mods, TASTEN[taste]


def tastenkuerzel_normal(text):
    """'Strg+Alt+J' -> 'ctrl+alt+j' (so steht es in config.json)."""
    zusatz, taste = tastenkuerzel_teile(text)
    return "+".join([*zusatz, taste])


def tastenkuerzel_anzeige(text):
    """'ctrl+alt+j' -> 'Strg+Alt+J'; leer -> ''."""
    if not (text or "").strip():
        return ""
    zusatz, taste = tastenkuerzel_teile(text)
    return "+".join(ANZEIGE.get(t, t.upper()) for t in [*zusatz, taste])


def tastenkuerzel_pruefen(text):
    """Fehlermeldung oder None. Buchstaben ohne Strg/Alt/Win würden beim Tippen auslösen."""
    try:
        zusatz, taste = tastenkuerzel_teile(text)
    except ValueError as e:
        return str(e)
    if not set(zusatz) - {"shift"} and not re.fullmatch(r"f\d+|pause", taste):
        return "Bitte mit Strg, Alt oder Win kombinieren - sonst löst die Taste beim normalen Tippen aus"
    return None


def taste_von_vk(vk):
    """Windows-Tastencode (wie tkinter ihn als event.keycode liefert) -> 'j' | None"""
    return _VK_NAME.get(vk)


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.RegisterHotKey.argtypes = [wt.HWND, ctypes.c_int, wt.UINT, wt.UINT]
_user32.UnregisterHotKey.argtypes = [wt.HWND, ctypes.c_int]
_user32.GetMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT]
_user32.PostThreadMessageW.argtypes = [wt.DWORD, wt.UINT, wt.WPARAM, wt.LPARAM]


def _fehlertext(code):
    if code == ERROR_HOTKEY_ALREADY_REGISTERED:
        return "schon von einem anderen Programm belegt"
    return f"Windows-Fehler {code}"


def tastenkuerzel_frei(text):
    """Kurz registrieren und wieder freigeben. -> (True, '') | (False, Grund)"""
    mods, vk = tastenkuerzel_lesen(text)
    if not _user32.RegisterHotKey(None, 0x4A45, mods | MOD_NOREPEAT, vk):
        return False, _fehlertext(ctypes.get_last_error())
    _user32.UnregisterHotKey(None, 0x4A45)
    return True, ""


class Tastenkuerzel:
    """Globales Tastenkürzel (Win32 RegisterHotKey) in eigenem Thread mit eigener Nachrichtenschleife.

    `rueckruf` läuft in diesem Thread - er soll nur ein Signal setzen (z. B. threading.Event.set),
    die eigentliche Arbeit macht der Thread, der das Signal abholt.
    """

    def __init__(self, text, rueckruf):
        self.mods, self.vk = tastenkuerzel_lesen(text)      # ValueError bei Unsinn
        self.anzeige = tastenkuerzel_anzeige(text)
        self.rueckruf = rueckruf
        self.fehler = None
        self._bereit = threading.Event()
        self._thread_id = None
        self._thread = threading.Thread(target=self._schleife, name="Tastenkuerzel", daemon=True)

    def starten(self, warten=3):
        """-> True, wenn das Kürzel registriert ist; sonst steht der Grund in self.fehler."""
        self._thread.start()
        if not self._bereit.wait(warten):
            self.fehler = "keine Antwort von Windows"
        return self.fehler is None

    def stoppen(self):
        if self._thread_id:
            _user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def _schleife(self):
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        if not _user32.RegisterHotKey(None, 1, self.mods | MOD_NOREPEAT, self.vk):
            self.fehler = _fehlertext(ctypes.get_last_error())
            self._bereit.set()
            return
        self._bereit.set()
        msg = wt.MSG()
        try:
            while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self.rueckruf()
        finally:
            _user32.UnregisterHotKey(None, 1)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for wort in sys.argv[1:] or ["hey jeff"]:
        fehlt = unbekannte_woerter(wort)
        print(f"{wort}: " + ("Wortschatz nicht lesbar" if fehlt is None else
                             f"unbekannt: {', '.join(fehlt)}" if fehlt else "alle Wörter bekannt"))
