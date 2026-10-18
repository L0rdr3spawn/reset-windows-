"""API-Keys – Fenster zum Speichern, Prüfen und Löschen der Keys für ask-cheap.

Keys landen im Windows-Anmeldeinformations-Manager (Ziel "ask-cheap:<VARNAME>"),
genau dort, wo ask-cheap sie sucht. Im Fenster wird nie der ganze Key angezeigt.
"""
import ctypes
import importlib.util
import os
import threading
import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("ask_cheap", os.path.join(HERE, "ask-cheap.py"))
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)

# (account, Überschrift, erwarteter Key-Anfang)
ACCOUNTS = [
    ("groq", "Groq – Account 1", "gsk_"),
    ("groq2", "Groq – Account 2", "gsk_"),
    ("gemini", "Google Gemini", "AIza"),
    ("openrouter", "OpenRouter", "sk-or-"),
]

BG, CARD, FIELD = "#1e1f22", "#2b2d31", "#383a40"
TEXT, MUTED = "#e8e8e8", "#9aa0a6"
GREEN, RED, BLUE, GREY = "#3ba55d", "#ed4245", "#5865f2", "#4e5058"
FONT, FONT_B, FONT_S = ("Segoe UI", 11), ("Segoe UI Semibold", 12), ("Segoe UI", 10)


def var_of(acct):
    return ac.key_var(*ac.parse_acct(acct))


def read_key(acct):
    return ac.wincred_read(var_of(acct))


def delete_key(acct):
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.CredDeleteW(f"ask-cheap:{var_of(acct)}", 1, 0)


def check_key(acct, key):
    """Prüft den Key mit GET /models (kostet keine Tokens). -> (ok, text)"""
    provider = ac.parse_acct(acct)[0]
    try:
        ac.http("GET", ac.PROVIDERS[provider]["url"] + "/models", key, timeout=15)
        return True, "funktioniert"
    except ac.ApiError as e:
        if e.status in (401, 403):
            return False, "Key ungültig oder gesperrt"
        if e.status == 0:
            return False, "keine Verbindung"
        return False, f"Fehler (HTTP {e.status})"


def button(parent, text, cmd, color=GREY, width=None):
    b = tk.Button(parent, text=text, command=cmd, font=FONT, fg="white", bg=color,
                  activebackground=color, activeforeground="white", relief="flat",
                  bd=0, padx=14, pady=5, cursor="hand2")
    if width:
        b.config(width=width)
    return b


class Row:
    def __init__(self, app, parent, acct, title, prefix):
        self.app, self.acct, self.prefix = app, acct, prefix
        card = tk.Frame(parent, bg=CARD, padx=16, pady=12)
        card.pack(fill="x", pady=6)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=title, font=FONT_B, fg=TEXT, bg=CARD).pack(side="left")
        self.delete_btn = button(top, "Löschen", self.delete, GREY)
        self.delete_btn.pack(side="right")
        self.stored = tk.Label(top, font=FONT_S, bg=CARD)
        self.stored.pack(side="right", padx=10)

        mid = tk.Frame(card, bg=CARD)
        mid.pack(fill="x", pady=(10, 0))
        self.entry = tk.Entry(mid, font=("Consolas", 11), show="•", bg=FIELD, fg=TEXT,
                              insertbackground=TEXT, relief="flat", bd=6)
        self.entry.pack(side="left", fill="x", expand=True, ipady=2)
        self.entry.bind("<Return>", lambda e: self.save())
        button(mid, "Einfügen", self.paste, GREY).pack(side="left", padx=(8, 0))
        button(mid, "Speichern", self.save, BLUE).pack(side="left", padx=(8, 0))

        self.msg = tk.Label(card, text="", font=FONT_S, fg=MUTED, bg=CARD, anchor="w")
        self.msg.pack(fill="x", pady=(6, 0))
        self.refresh()

    def refresh(self):
        key = read_key(self.acct)
        if key:
            self.stored.config(text=f"● gespeichert  (…{key[-4:]})", fg=GREEN)
            if not self.delete_btn.winfo_manager():
                self.delete_btn.pack(side="right", before=self.stored)
        else:
            self.stored.config(text="○ kein Key", fg=MUTED)
            self.delete_btn.pack_forget()

    def say(self, text, color=MUTED):
        self.msg.config(text=text, fg=color)

    def paste(self):
        try:
            text = self.app.root.clipboard_get().strip()
        except tk.TclError:
            text = ""
        if not text:
            return self.say("Zwischenablage ist leer – Key erst im Browser kopieren.", RED)
        self.entry.delete(0, "end")
        self.entry.insert(0, text)
        self.say("Eingefügt – jetzt „Speichern“ drücken.")

    def save(self):
        key = self.entry.get().strip()
        if not key:
            return self.say("Erst den Key einfügen.", RED)
        problem = ac.key_problem(key)
        if problem:
            return self.say("Das sieht nicht nach einem Key aus (zu kurz oder Sonderzeichen).", RED)
        if not key.startswith(self.prefix):
            return self.say(f"Dieser Key passt nicht hierher – er sollte mit „{self.prefix}“ anfangen.", RED)
        for other, title, _ in ACCOUNTS:
            if other != self.acct and read_key(other) == key:
                return self.say(f"Dieser Key ist schon bei „{title}“ gespeichert.", RED)
        ac.wincred_write(var_of(self.acct), key)
        self.entry.delete(0, "end")
        try:  # Key nicht in der Zwischenablage liegen lassen
            if self.app.root.clipboard_get().strip() == key:
                self.app.root.clipboard_clear()
        except tk.TclError:
            pass
        self.refresh()
        self.test()

    def delete(self):
        delete_key(self.acct)
        self.refresh()
        self.say("Gelöscht.")

    def test(self):
        key = read_key(self.acct)
        if not key:
            return self.say("")
        self.say("Wird geprüft …")

        def work():
            ok, text = check_key(self.acct, key)
            self.app.root.after(0, lambda: self.say(("✓ " if ok else "✗ ") + text, GREEN if ok else RED))
        threading.Thread(target=work, daemon=True).start()


class App:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        self.root = tk.Tk()
        self.root.title("API-Keys")
        self.root.configure(bg=BG)
        self.root.minsize(620, 0)

        wrap = tk.Frame(self.root, bg=BG, padx=20, pady=16)
        wrap.pack(fill="both", expand=True)
        tk.Label(wrap, text="API-Keys für ask-cheap", font=("Segoe UI Semibold", 15),
                 fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(wrap, text="Key im Browser kopieren  →  „Einfügen“  →  „Speichern“. "
                            "Gespeichert wird sicher in Windows.",
                 font=FONT_S, fg=MUTED, bg=BG).pack(anchor="w", pady=(2, 8))

        self.rows = [Row(self, wrap, *a) for a in ACCOUNTS]

        bottom = tk.Frame(wrap, bg=BG)
        bottom.pack(fill="x", pady=(10, 0))
        button(bottom, "Alle Keys prüfen", self.test_all, BLUE).pack(side="left")
        button(bottom, "Schließen", self.root.destroy, GREY).pack(side="right")

        self.root.after(200, self.test_all)

    def test_all(self):
        for r in self.rows:
            r.test()


if __name__ == "__main__":
    App().root.mainloop()
