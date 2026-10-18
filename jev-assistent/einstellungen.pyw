"""einstellungen.pyw - Bedienoberfläche für den Sprachassistenten ("Jeff Einstellungen").

Öffnen: Doppelklick auf "Jeff Einstellungen" (Desktop oder dieser Ordner). Die Verknüpfung
startet pythonw.exe, also ohne Konsolenfenster.

Einstellbar: Name des Assistenten, Weckwort, Weckwort-Empfindlichkeit, globales
Tastenkürzel, Sprachausgabe und Autostart. Dazu Status, Neustart und Stoppen.
Geschrieben wird nur in config.json - alle anderen Einträge bleiben, wie sie sind.

  pythonw einstellungen.pyw
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BASIS = Path(__file__).resolve().parent
sys.path.insert(0, str(BASIS))
import aktivierung  # noqa: E402 - erst nach sys.path

CONFIG_DATEI = BASIS / "config.json"
STATUS_DATEI = BASIS / "jev.status"
SKRIPT = BASIS / "jev_assistent.py"
MUTEX_NAME = "Local\\JevAssistent"          # wie in jev_assistent.py

_py = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python312"
PY_ORDNER = _py if (_py / "pythonw.exe").exists() else Path(sys.executable).parent
PYTHON = PY_ORDNER / "python.exe"
PYTHONW = PY_ORDNER / "pythonw.exe"
OHNE_FENSTER = 0x08000000                  # CREATE_NO_WINDOW
LOSGELOEST = 0x00000008 | 0x00000200       # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

# Farben wie die Claude-Leiste
BG = "#1f1f23"
KARTE = "#26262b"
RAND = "#34343b"
FELD = "#2e2e34"
FG = "#f2f2f2"
MUTED = "#8a8a93"
ACCENT = "#d97757"
ACCENT_HELL = "#e48c6f"
GRUEN = "#7cc48a"
GELB = "#e5b85c"
ROT = "#e2675f"
SCHRIFT = "Segoe UI"


# --- Jeff-Prozess --------------------------------------------------------

def jeff_laeuft():
    """Gleiche Sperre wie jev_assistent.py: der Mutex verschwindet mit dem Prozess."""
    k32 = ctypes.windll.kernel32
    k32.OpenMutexW.restype = ctypes.c_void_p
    k32.OpenMutexW.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_wchar_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    h = k32.OpenMutexW(0x00100000, False, MUTEX_NAME)     # SYNCHRONIZE
    if h:
        k32.CloseHandle(h)
    return bool(h)


def jeff_zustand():
    """'hört zu auf ...' / 'lädt' / 'Mikrofon-Fehler: ...' aus jev.status (ohne Zeitstempel)."""
    try:
        return STATUS_DATEI.read_text(encoding="utf-8")[20:].strip()
    except OSError:
        return ""


def jeff_stoppen():
    r = subprocess.run([str(PYTHON), str(SKRIPT), "--stop"], cwd=BASIS, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=OHNE_FENSTER)
    return (r.stdout or r.stderr).strip()


def jeff_starten():
    """Wie 'Jeff starten.cmd': pythonw losgelöst, ohne geerbte Ein-/Ausgabe."""
    subprocess.Popen([str(PYTHONW), str(SKRIPT)], cwd=BASIS, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                     creationflags=LOSGELOEST)


def autostart_modul():
    """autostart.py erst bei Bedarf laden - ist es kaputt, öffnet sich das Fenster trotzdem.
    -> (Modul, None) | (None, Grund)"""
    try:
        import autostart
        for f in ("ist_an", "ein", "aus"):
            if not callable(getattr(autostart, f, None)):
                return None, f"autostart.{f}() fehlt"
        return autostart, None
    except Exception as e:  # noqa: BLE001 - egal warum, dann eben ohne Autostart-Schalter
        return None, str(e)[:80]


# --- config.json -----------------------------------------------------------

def config_lesen():
    return json.loads(CONFIG_DATEI.read_text(encoding="utf-8"))


def config_schreiben(aenderungen):
    """Nur die genannten Schlüssel ändern; Reihenfolge, Einrückung (2) und Umlaute bleiben."""
    roh = CONFIG_DATEI.read_text(encoding="utf-8")
    alt = json.loads(roh)
    neu = {}
    if "name" in aenderungen and "name" not in alt:
        neu["name"] = aenderungen["name"]                     # neuer Schlüssel nach oben
    for k, v in alt.items():
        neu[k] = aenderungen.get(k, v)
        if k == "weckwort_sicherheit" and "hotkey" in aenderungen and "hotkey" not in alt:
            neu["hotkey"] = aenderungen["hotkey"]
    for k, v in aenderungen.items():
        neu.setdefault(k, v)
    text = json.dumps(neu, indent=2, ensure_ascii=False) + ("\n" if roh.endswith("\n") else "")
    tmp = CONFIG_DATEI.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, CONFIG_DATEI)


# --- Bausteine ---------------------------------------------------------------

class Schalter(tk.Canvas):
    """Kippschalter im Stil moderner Einstellungs-Apps."""

    def __init__(self, master, variable, s=1.0, bg=KARTE):
        self.b, self.h = int(42 * s), int(24 * s)
        super().__init__(master, width=self.b, height=self.h, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.var = variable
        self.aktiv = True
        self.bind("<Button-1>", self._klick)
        variable.trace_add("write", lambda *_: self._zeichnen())
        self._zeichnen()

    def sperren(self, gesperrt=True):
        self.aktiv = not gesperrt
        self.config(cursor="arrow" if gesperrt else "hand2")
        self._zeichnen()

    def _klick(self, _e=None):
        if self.aktiv:
            self.var.set(not self.var.get())

    def _zeichnen(self):
        self.delete("all")
        an, b, h = bool(self.var.get()), self.b, self.h
        farbe = (ACCENT if an else "#4a4a53") if self.aktiv else "#38383e"
        r = h // 2
        self.create_oval(1, 1, h - 1, h - 1, fill=farbe, outline=farbe)
        self.create_oval(b - h + 1, 1, b - 1, h - 1, fill=farbe, outline=farbe)
        self.create_rectangle(r, 1, b - r, h - 1, fill=farbe, outline=farbe)
        x = b - r if an else r
        k = r - max(3, h // 8)
        self.create_oval(x - k, r - k, x + k, r + k, fill="#ffffff" if self.aktiv else "#6a6a72", outline="")


class Regler(tk.Canvas):
    """Schieberegler: Spur, gefüllter Anteil in Akzentfarbe, runder Knopf (tk.Scale sieht dunkel kaum aus)."""

    def __init__(self, master, variable, von, bis, s=1.0, schritt=0.01, bg=KARTE):
        self.h, self.r = int(24 * s), int(8 * s)
        super().__init__(master, height=self.h, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.var, self.von, self.bis, self.schritt = variable, von, bis, schritt
        for ereignis in ("<Button-1>", "<B1-Motion>"):
            self.bind(ereignis, self._ziehen)
        self.bind("<Configure>", lambda e: self._zeichnen())
        variable.trace_add("write", lambda *_: self._zeichnen())

    def _ziehen(self, e):
        b = max(1, self.winfo_width() - 2 * self.r)
        anteil = min(1.0, max(0.0, (e.x - self.r) / b))
        wert = self.von + anteil * (self.bis - self.von)
        self.var.set(round(round(wert / self.schritt) * self.schritt, 2))

    def _zeichnen(self):
        self.delete("all")
        b, m, r = self.winfo_width(), self.h // 2, self.r
        try:
            wert = float(self.var.get())
        except (tk.TclError, ValueError):
            return
        x = r + (b - 2 * r) * (min(self.bis, max(self.von, wert)) - self.von) / (self.bis - self.von)
        dicke = max(4, r // 2)
        self.create_line(r, m, b - r, m, fill=FELD, width=dicke, capstyle="round")
        self.create_line(r, m, x, m, fill=ACCENT, width=dicke, capstyle="round")
        self.create_oval(x - r, m - r, x + r, m + r, fill="#ffffff", outline=ACCENT, width=2)


def knopf(master, text, befehl, haupt=False):
    farbe, hover = (ACCENT, ACCENT_HELL) if haupt else (FELD, "#3a3a42")
    b = tk.Button(master, text=text, command=befehl, font=(SCHRIFT, 10, "bold" if haupt else "normal"),
                  bg=farbe, fg="#ffffff" if haupt else FG, activebackground=hover,
                  activeforeground="#ffffff" if haupt else FG, relief="flat", bd=0, highlightthickness=0,
                  padx=14, pady=6, cursor="hand2", disabledforeground=MUTED)
    b.bind("<Enter>", lambda e: b.config(bg=hover) if str(b["state"]) != "disabled" else None)
    b.bind("<Leave>", lambda e: b.config(bg=farbe))
    return b


def eingabe(master, variable):
    return tk.Entry(master, textvariable=variable, font=(SCHRIFT, 11), bg=FELD, fg=FG, insertbackground=FG,
                    relief="flat", bd=0, highlightthickness=1, highlightbackground=RAND, highlightcolor=ACCENT,
                    selectbackground=ACCENT, selectforeground="#ffffff")


# --- Fenster -------------------------------------------------------------------

class Einstellungen:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.report_callback_exception = self._absturz
        self.s = max(1.0, self.root.winfo_fpixels("1i") / 96)

        self.cfg = config_lesen()
        self.gespeichert_name = aktivierung.name(self.cfg)
        self.gespeichert_kuerzel = (self.cfg.get("hotkey") or "").strip()
        self.name_vorher = self.gespeichert_name

        self.name_var = tk.StringVar(value=self.gespeichert_name)
        self.weckwort_var = tk.StringVar(value=aktivierung.weckwort(self.cfg))
        self.sicherheit_var = tk.DoubleVar(value=float(self.cfg.get("weckwort_sicherheit", 0.65)))
        self.kuerzel = self.gespeichert_kuerzel
        self.sprache_var = tk.BooleanVar(value=bool(self.cfg.get("sprachausgabe", True)))
        self.autostart, self.autostart_fehler = autostart_modul()
        self.autostart_war = False
        if self.autostart:
            try:
                self.autostart_war = bool(self.autostart.ist_an())
            except Exception as e:  # noqa: BLE001
                self.autostart, self.autostart_fehler = None, str(e)[:80]
        self.autostart_var = tk.BooleanVar(value=self.autostart_war)
        self.nimmt_auf = False
        self.beschaeftigt = False
        self._pruef_auftrag = None

        self._aufbauen()
        self.name_var.trace_add("write", self._name_geaendert)
        self.weckwort_var.trace_add("write", lambda *_: self._weckwort_bald_pruefen())
        self.sicherheit_var.trace_add("write", lambda *_: self._sicherheit_zeigen())
        self._titel_setzen()
        self._weckwort_pruefen()
        self._sicherheit_zeigen()
        self._kuerzel_zeigen()
        self._status_aktualisieren()
        self.root.after(30, self._dunkle_titelleiste)
        self._mittig()

    # -- Aufbau
    def _px(self, n):
        return int(n * self.s)

    def _karte(self, titel):
        rahmen = tk.Frame(self.root, bg=KARTE, highlightthickness=1, highlightbackground=RAND)
        rahmen.pack(fill="x", padx=self._px(20), pady=(0, self._px(12)))
        innen = tk.Frame(rahmen, bg=KARTE)
        innen.pack(fill="x", padx=self._px(16), pady=self._px(12))
        tk.Label(innen, text=titel.upper(), font=(SCHRIFT, 8, "bold"), fg=ACCENT, bg=KARTE).pack(anchor="w")
        return innen

    def _beschriftung(self, master, text, oben=10):
        tk.Label(master, text=text, font=(SCHRIFT, 10), fg=FG, bg=KARTE).pack(anchor="w", pady=(self._px(oben), 2))

    def _hinweis(self, master, text="", farbe=MUTED):
        lbl = tk.Label(master, text=text, font=(SCHRIFT, 9), fg=farbe, bg=KARTE, justify="left",
                       anchor="w", wraplength=self._px(470))
        lbl.pack(anchor="w", fill="x", pady=(3, 0))
        return lbl

    def _aufbauen(self):
        px = self._px
        kopf = tk.Frame(self.root, bg=BG)
        kopf.pack(fill="x", padx=px(20), pady=(px(18), px(12)))
        tk.Label(kopf, text="✳", font=("Segoe UI Symbol", 22), fg=ACCENT, bg=BG).pack(side="left", padx=(0, px(10)))
        texte = tk.Frame(kopf, bg=BG)
        texte.pack(side="left")
        self.ueberschrift = tk.Label(texte, text="", font=(SCHRIFT, 17, "bold"), fg=FG, bg=BG)
        self.ueberschrift.pack(anchor="w")
        self.unterzeile = tk.Label(texte, text="", font=(SCHRIFT, 9), fg=MUTED, bg=BG)
        self.unterzeile.pack(anchor="w")

        # Name und Weckwort
        k = self._karte("Name & Aktivierung")
        self._beschriftung(k, "Name des Assistenten", oben=8)
        eingabe(k, self.name_var).pack(fill="x", ipady=px(5), ipadx=px(6))
        self.name_hinweis = self._hinweis(k)

        self._beschriftung(k, "Aktivierungswort (Weckwort)")
        eingabe(k, self.weckwort_var).pack(fill="x", ipady=px(5), ipadx=px(6))
        self.weckwort_hinweis = self._hinweis(k)

        zeile = tk.Frame(k, bg=KARTE)
        zeile.pack(fill="x", pady=(px(12), 0))
        tk.Label(zeile, text="Weckwort-Empfindlichkeit", font=(SCHRIFT, 10), fg=FG, bg=KARTE).pack(side="left")
        self.sicherheit_wert = tk.Label(zeile, text="", font=(SCHRIFT, 10, "bold"), fg=ACCENT, bg=KARTE)
        self.sicherheit_wert.pack(side="right")
        Regler(k, self.sicherheit_var, 0.4, 0.9, self.s).pack(fill="x", pady=(px(4), 0))
        enden = tk.Frame(k, bg=KARTE)
        enden.pack(fill="x")
        tk.Label(enden, text="◀ reagiert leichter", font=(SCHRIFT, 8), fg=MUTED, bg=KARTE).pack(side="left")
        tk.Label(enden, text="weniger Fehlalarme ▶", font=(SCHRIFT, 8), fg=MUTED, bg=KARTE).pack(side="right")

        # Tastenkürzel
        k = self._karte("Tastenkürzel")
        zeile = tk.Frame(k, bg=KARTE)
        zeile.pack(fill="x", pady=(px(8), 0))
        self.kuerzel_feld = tk.Label(zeile, text="", font=(SCHRIFT, 11, "bold"), fg=FG, bg=FELD, padx=px(12),
                                     pady=px(5), highlightthickness=1, highlightbackground=RAND,
                                     highlightcolor=ACCENT, takefocus=0)
        self.kuerzel_feld.pack(side="left", fill="x", expand=True)
        self.kuerzel_feld.bind("<KeyPress>", self._taste_gedrueckt)
        self.kuerzel_feld.bind("<FocusOut>", lambda e: self._aufnahme_beenden() if self.nimmt_auf else None)
        self.loeschen_knopf = knopf(zeile, "Löschen", self._kuerzel_loeschen)
        self.loeschen_knopf.pack(side="right", padx=(px(6), 0))
        self.aufnehmen_knopf = knopf(zeile, "Taste aufnehmen", self._aufnahme_starten)
        self.aufnehmen_knopf.pack(side="right", padx=(px(8), 0))
        self.kuerzel_hinweis = self._hinweis(k)

        # Allgemein
        k = self._karte("Allgemein")
        self._schalter_zeile(k, "Sprachausgabe", "Antworten und Rückfragen laut vorlesen", self.sprache_var)
        self.autostart_schalter, self.autostart_hinweis = self._schalter_zeile(
            k, "Mit Windows starten", "Startet beim Anmelden unsichtbar im Hintergrund", self.autostart_var)
        if not self.autostart:
            self.autostart_schalter.sperren()
            self.autostart_hinweis.config(text=f"Autostart-Modul nicht verfügbar ({self.autostart_fehler})")

        # Status und Knöpfe
        fuss = tk.Frame(self.root, bg=BG)
        fuss.pack(fill="x", padx=px(20), pady=(px(2), px(18)))
        statuszeile = tk.Frame(fuss, bg=BG)
        statuszeile.pack(fill="x")
        self.status_punkt = tk.Label(statuszeile, text="●", font=(SCHRIFT, 11), fg=MUTED, bg=BG)
        self.status_punkt.pack(side="left")
        self.status_text = tk.Label(statuszeile, text="", font=(SCHRIFT, 9), fg=FG, bg=BG, anchor="w",
                                    justify="left", wraplength=px(480))
        self.status_text.pack(side="left", fill="x", padx=(px(6), 0))

        knoepfe = tk.Frame(fuss, bg=BG)
        knoepfe.pack(fill="x", pady=(px(10), 0))
        self.speichern_knopf = knopf(knoepfe, "Speichern", self.speichern)
        self.speichern_knopf.pack(side="left")
        self.neustart_knopf = knopf(knoepfe, "", self.speichern_und_neustarten, haupt=True)
        self.neustart_knopf.pack(side="left", padx=(px(8), 0))
        self.stopp_knopf = knopf(knoepfe, "", self._stoppen_oder_starten)
        self.stopp_knopf.pack(side="right")
        self.meldung = tk.Label(fuss, text="", font=(SCHRIFT, 9), fg=MUTED, bg=BG, anchor="w", justify="left",
                                wraplength=px(500))
        self.meldung.pack(fill="x", pady=(px(8), 0))

    def _schalter_zeile(self, master, titel, text, variable):
        zeile = tk.Frame(master, bg=KARTE)
        zeile.pack(fill="x", pady=(self._px(10), 0))
        schalter = Schalter(zeile, variable, self.s)
        schalter.pack(side="right", padx=(self._px(10), 0))
        links = tk.Frame(zeile, bg=KARTE)
        links.pack(side="left", fill="x", expand=True)
        tk.Label(links, text=titel, font=(SCHRIFT, 10), fg=FG, bg=KARTE).pack(anchor="w")
        hinweis = tk.Label(links, text=text, font=(SCHRIFT, 9), fg=MUTED, bg=KARTE, anchor="w")
        hinweis.pack(anchor="w")
        return schalter, hinweis

    def _mittig(self):
        self.root.update_idletasks()
        b, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - b) // 2
        y = max(0, (self.root.winfo_screenheight() - h) // 2 - self._px(30))
        self.root.geometry(f"+{x}+{y}")

    def _dunkle_titelleiste(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            wert = ctypes.c_int(1)
            for attribut in (20, 19):          # DWMWA_USE_IMMERSIVE_DARK_MODE (neu / alt)
                if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribut, ctypes.byref(wert), 4) == 0:
                    break
        except (AttributeError, OSError):
            pass

    def _absturz(self, art, wert, tb):
        import traceback
        text = "".join(traceback.format_exception(art, wert, tb))
        messagebox.showerror("Fehler", text[-1500:], parent=self.root)

    # -- Name
    def _name(self):
        return " ".join(self.name_var.get().split())

    def _titel_setzen(self):
        n = self._name() or self.gespeichert_name
        self.root.title(f"{n} – Einstellungen")
        self.ueberschrift.config(text=f"{n} – Einstellungen")
        self.unterzeile.config(text=f"Name, Aktivierung und Start von {n}")
        self.neustart_knopf.config(text=f"Speichern & {n} neu starten")
        self._status_aktualisieren(nur_text=True)

    def _name_geaendert(self, *_):
        neu = self._name()
        self._titel_setzen()
        if not neu:
            self.name_hinweis.config(text="Bitte einen Namen eingeben.", fg=GELB)
            return
        # "hey <alter Name>" wandert mit; ein eigenes Weckwort bleibt unangetastet
        if aktivierung.normal(self.weckwort_var.get()) == aktivierung.standard_weckwort(self.name_vorher):
            self.weckwort_var.set(aktivierung.standard_weckwort(neu))
            angepasst = True
        else:
            angepasst = False
        self.name_vorher = neu
        if neu != self.gespeichert_name:
            self.name_hinweis.config(fg=MUTED, text=f"So nennt er sich in Ansagen, im Log und gegenüber Claude."
                                     + (f" Weckwort angepasst auf „{aktivierung.standard_weckwort(neu)}“."
                                        if angepasst else ""))
        else:
            self.name_hinweis.config(text="", fg=MUTED)

    # -- Weckwort
    def _weckwort_bald_pruefen(self):
        if self._pruef_auftrag:
            self.root.after_cancel(self._pruef_auftrag)
        self._pruef_auftrag = self.root.after(350, self._weckwort_pruefen)

    def _weckwort_pruefen(self):
        """Hinweis unter dem Weckwort. -> Liste unbekannter Wörter"""
        self._pruef_auftrag = None
        w = aktivierung.normal(self.weckwort_var.get())
        n = self._name() or self.gespeichert_name
        if not w:
            self.weckwort_hinweis.config(text=f"Bitte ein Weckwort eingeben, z. B. „hey {n.lower()}“.", fg=GELB)
            return []
        fehlt = aktivierung.unbekannte_woerter(w)
        if fehlt is None:
            self.weckwort_hinweis.config(text="Der Wortschatz der Weckwort-Erkennung ist nicht lesbar - "
                                              "das Weckwort bleibt ungeprüft.", fg=GELB)
            return []
        if fehlt:
            if len(fehlt) == 1:
                was = f"Das Wort „{fehlt[0]}“ kennt"
            else:
                was = "Die Wörter " + ", ".join(f"„{x}“" for x in fehlt) + " kennt"
            self.weckwort_hinweis.config(fg=ROT, text=f"⚠ {was} die Weckwort-Erkennung nicht - darauf würde {n} "
                                                      "nie reagieren. Probier eine andere Schreibweise oder ein anderes Wort.")
            return fehlt
        tipp = (f" Tipp: Zwei Wörter wie „hey {w}“ lösen seltener aus Versehen aus." if len(w.split()) == 1 else "")
        self.weckwort_hinweis.config(fg=GRUEN if not tipp else GELB,
                                     text=f"✓ Die Weckwort-Erkennung kennt „{w}“.{tipp}")
        return []

    def _sicherheit_zeigen(self):
        self.sicherheit_wert.config(text=f"{self.sicherheit_var.get():.2f}")

    # -- Tastenkürzel
    def _kuerzel_zeigen(self, hinweis=None, farbe=MUTED):
        n = self._name() or self.gespeichert_name
        if self.nimmt_auf:
            self.kuerzel_feld.config(text="Drück jetzt die Tastenkombination …", fg=ACCENT, highlightbackground=ACCENT)
        elif self.kuerzel:
            self.kuerzel_feld.config(text=aktivierung.tastenkuerzel_anzeige(self.kuerzel), fg=FG,
                                     highlightbackground=RAND)
        else:
            self.kuerzel_feld.config(text="aus", fg=MUTED, highlightbackground=RAND)
        self.loeschen_knopf.config(state="normal" if self.kuerzel else "disabled")
        if hinweis is None:
            hinweis = (f"Drückst du das Kürzel irgendwo in Windows, piept {n} und hört sofort zu - ohne Weckwort."
                       if self.kuerzel else "Optional: ein Tastenkürzel, das zuhören lässt, ohne das Weckwort zu sagen.")
        self.kuerzel_hinweis.config(text=hinweis, fg=farbe)

    def _aufnahme_starten(self):
        self.nimmt_auf = True
        self.aufnehmen_knopf.config(text="Abbrechen", command=self._aufnahme_beenden)
        self.kuerzel_feld.focus_set()
        self._kuerzel_zeigen("Zum Beispiel Strg+Alt+J oder Strg+Umschalt+F8. Esc bricht ab.")

    def _aufnahme_beenden(self, hinweis=None, farbe=MUTED):
        self.nimmt_auf = False
        self.aufnehmen_knopf.config(text="Taste aufnehmen", command=self._aufnahme_starten)
        self._kuerzel_zeigen(hinweis, farbe)

    @staticmethod
    def _gedrueckt(vk):
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

    def _taste_gedrueckt(self, e):
        if not self.nimmt_auf:
            return None
        vk = e.keycode                      # unter Windows ist das der virtuelle Tastencode
        if vk in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x14, 0x90):
            return "break"                  # nur Strg/Alt/Umschalt/Win: auf die eigentliche Taste warten
        zusatz = []
        if e.state & 0x4 or self._gedrueckt(0x11):
            zusatz.append("ctrl")
        if e.state & 0x1 or self._gedrueckt(0x10):
            zusatz.append("shift")
        if e.state & 0x20000 or self._gedrueckt(0x12):
            zusatz.append("alt")
        if self._gedrueckt(0x5B) or self._gedrueckt(0x5C):
            zusatz.append("win")
        if vk == 0x1B and not zusatz:
            self._aufnahme_beenden()
            return "break"
        taste = aktivierung.taste_von_vk(vk)
        if not taste:
            self._aufnahme_beenden(f"Diese Taste ({e.keysym}) geht nicht - nimm einen Buchstaben, eine Ziffer "
                                   "oder F1-F24.", GELB)
            return "break"
        kombi = "+".join([*zusatz, taste])
        fehler = aktivierung.tastenkuerzel_pruefen(kombi)
        if not fehler and not (kombi == self.gespeichert_kuerzel and jeff_laeuft()):
            frei, grund = aktivierung.tastenkuerzel_frei(kombi)    # hält der laufende Jeff es selbst, kommt es hier nie an
            if not frei:
                fehler = f"{aktivierung.tastenkuerzel_anzeige(kombi)} ist {grund}."
        if fehler:
            self._aufnahme_beenden(f"⚠ {fehler}", ROT)
            return "break"
        self.kuerzel = aktivierung.tastenkuerzel_normal(kombi)
        self._aufnahme_beenden()
        self._ungespeichert()
        return "break"

    def _kuerzel_loeschen(self):
        self.kuerzel = ""
        self._aufnahme_beenden()
        self._ungespeichert()

    def _ungespeichert(self):
        self.meldung.config(text="Noch nicht gespeichert.", fg=MUTED)

    # -- Status
    def _status_aktualisieren(self, nur_text=False):
        n = self._name() or self.gespeichert_name
        laeuft = jeff_laeuft()
        zustand = jeff_zustand() if laeuft else ""
        if not laeuft:
            punkt, text = MUTED, f"{n} läuft nicht."
        elif "hört zu" in zustand:
            punkt, text = GRUEN, f"{n} läuft und {zustand}."
        elif "Fehler" in zustand:
            punkt, text = ROT, f"{n} läuft, aber: {zustand}"
        else:
            punkt, text = GELB, f"{n} lädt … (Whisper braucht etwa 30 Sekunden)"
        self.status_punkt.config(fg=punkt)
        self.status_text.config(text=text)
        if not self.beschaeftigt:
            self.stopp_knopf.config(text=f"{n} stoppen" if laeuft else f"{n} starten", state="normal")
        if not nur_text:
            self.root.after(1500, self._status_aktualisieren)

    # -- Speichern
    def speichern(self, still=False):
        """config.json schreiben (und Autostart umstellen). -> True, wenn gespeichert"""
        if self.nimmt_auf:
            self._aufnahme_beenden()
        name = self._name()
        weckwort = aktivierung.normal(self.weckwort_var.get())
        if not name:
            messagebox.showwarning("Name fehlt", "Bitte einen Namen für den Assistenten eingeben.", parent=self.root)
            return False
        if not weckwort:
            messagebox.showwarning("Weckwort fehlt", "Bitte ein Weckwort eingeben.", parent=self.root)
            return False
        fehlt = self._weckwort_pruefen()
        if fehlt and not messagebox.askyesno(
                "Unbekanntes Wort",
                f"„{', '.join(fehlt)}“ kennt die Weckwort-Erkennung nicht. {name} würde auf „{weckwort}“ "
                f"nicht reagieren{' (nur auf das Tastenkürzel)' if self.kuerzel else ''}.\n\nTrotzdem speichern?",
                parent=self.root):
            return False
        aenderungen = {"name": name, "weckwort": weckwort,
                       "weckwort_sicherheit": round(float(self.sicherheit_var.get()), 2),
                       "hotkey": self.kuerzel, "sprachausgabe": bool(self.sprache_var.get())}
        try:
            config_schreiben(aenderungen)
        except (OSError, ValueError) as e:
            messagebox.showerror("Speichern fehlgeschlagen", f"config.json konnte nicht geschrieben werden:\n{e}",
                                 parent=self.root)
            return False
        name_neu = name != self.gespeichert_name
        self.gespeichert_name, self.gespeichert_kuerzel, self.name_vorher = name, self.kuerzel, name
        self.name_hinweis.config(text="")
        self._titel_setzen()
        meldungen = ["Gespeichert."]
        if not still and jeff_laeuft():
            meldungen.append(f"Die Änderungen gelten, sobald {name} neu startet.")
        self._autostart_anwenden(name_neu, meldungen)
        self.meldung.config(text=" ".join(meldungen), fg=GRUEN)
        return True

    def _autostart_anwenden(self, name_neu, meldungen):
        if not self.autostart:
            return
        soll = bool(self.autostart_var.get())
        if soll != self.autostart_war or (soll and name_neu):
            # ein() baut den Starter mit dem neuen Namen neu - dauert ein paar Sekunden
            aufruf = self.autostart.ein if soll else self.autostart.aus
            self.autostart_war = soll
            meldungen.append("Autostart wird umgestellt …")
            threading.Thread(target=self._im_hintergrund, args=(aufruf,), daemon=True).start()

    def _im_hintergrund(self, aufruf):
        try:
            text = aufruf()
        except Exception as e:  # noqa: BLE001
            text = f"Autostart: {e}"
        self.root.after(0, lambda: self.meldung.config(text=f"Gespeichert. {text}", fg=FG))

    # -- Neustart / Stopp
    def speichern_und_neustarten(self):
        if self.beschaeftigt or not self.speichern(still=True):
            return
        self._arbeiten(f"{self.gespeichert_name} startet neu …", neu_starten=True)

    def _stoppen_oder_starten(self):
        if self.beschaeftigt:
            return
        if jeff_laeuft():
            self._arbeiten(f"{self.gespeichert_name} wird gestoppt …", neu_starten=False)
        else:
            self._arbeiten(f"{self.gespeichert_name} startet …", neu_starten=True, stoppen=False)

    def _arbeiten(self, text, neu_starten, stoppen=True):
        self.beschaeftigt = True
        for b in (self.neustart_knopf, self.stopp_knopf, self.speichern_knopf):
            b.config(state="disabled")
        self.meldung.config(text=text, fg=MUTED)

        def ablauf():
            try:
                if stoppen:
                    jeff_stoppen()
                if neu_starten:
                    jeff_starten()
                    ergebnis = (f"{self.gespeichert_name} startet im Hintergrund. Whisper lädt etwa 30 Sekunden, "
                                "dann wird der Punkt grün.")
                else:
                    ergebnis = f"{self.gespeichert_name} ist gestoppt."
            except Exception as e:  # noqa: BLE001
                ergebnis = f"Hat nicht geklappt: {e}"
            self.root.after(0, self._fertig, ergebnis)

        threading.Thread(target=ablauf, daemon=True).start()

    def _fertig(self, text):
        self.beschaeftigt = False
        for b in (self.neustart_knopf, self.stopp_knopf, self.speichern_knopf):
            b.config(state="normal")
        self.meldung.config(text=text, fg=FG)
        self._status_aktualisieren(nur_text=True)

    def starten(self):
        self.root.mainloop()


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # scharfe Schrift bei 125/150 % Skalierung
    except (AttributeError, OSError):
        pass
    Einstellungen().starten()


if __name__ == "__main__":
    main()
