"""Claude-Leiste: schwebende Suchleiste mit Claude.

Alt+Leertaste öffnet die Leiste, Befehl eintippen, Enter. Claude entscheidet,
was passiert (Website öffnen, Programm starten, Ordner öffnen, Frage beantworten).
Esc schließt die Leiste. "beenden" eintippen oder Rechtsklick auf den Stern beendet das Programm.

Nutzt die installierte Claude-Code-CLI (dein Claude-Abo), kein API-Key nötig.

Modellwahl: Zuerst bewertet Haiku (schnell) die Aufgabe. Einfaches (Websites, Programme,
Ordner, kurze Fakten) erledigt Haiku selbst. Ist die Aufgabe zu schwer, gibt Haiku sie
an Sonnet oder Opus mit passender Denkstufe (Effort) weiter, z. B. „→ Opus · max“.

Manuell festlegen mit Präfixen am Anfang (kombinierbar, überspringen Haikus Bewertung):
  !haiku  !sonnet  !opus            Modell wählen
  !low  !medium  !high  !xhigh  !max  Denkstufe wählen (auch: !niedrig, !mittel, !hoch)
  !ultra                            = Opus mit höchster Stufe (max)
Beispiele: „!opus !max beweise, dass ...“, „!sonnet !low fasse zusammen: ...“, „!ultra ...“
Nur eine Stufe ohne Modell (z. B. „!high frage“) nutzt ESCALATE_MODEL.
"""
import ctypes
import ctypes.wintypes as wt
import glob
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import tkinter.font as tkfont
import urllib.parse
import webbrowser

# ---------------------------------------------------------------- Einstellungen
MODEL = "haiku"  # Triage-Modell: schnell, bewertet jede Aufgabe und eskaliert bei Bedarf
ESCALATE_MODEL = "sonnet"  # Standard, falls Haiku/Präfix kein gültiges Modell nennt
ESCALATE_EFFORT = "high"  # Standard, falls Haiku/Präfix keine gültige Stufe nennt
MODELS = ("haiku", "sonnet", "opus")  # Aliase, die `claude --model` versteht
EFFORTS = ("low", "medium", "high", "xhigh", "max")  # laut `claude --help` (--effort)
TIMEOUT_FAST = 120  # Sekunden für Haiku
TIMEOUT_ESCALATED = 180  # Sekunden für Stufe low/medium
TIMEOUT_DEEP = 300  # Sekunden für Stufe high/xhigh/max
ANSWER_MAX_HEIGHT = 420  # Pixel; längere Antworten werden gekürzt (Klick kopiert alles)
WIDTH = 640
BAR_HEIGHT = 60
BG = "#1f1f23"
FG = "#f2f2f2"
MUTED = "#8a8a93"
ACCENT = "#d97757"
TRANSPARENT = "#010203"
FONT = ("Segoe UI", 15)
ANSWER_FONT = ("Segoe UI", 11)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x4000
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
CREATE_NO_WINDOW = 0x08000000
HOTKEYS = [
    (MOD_ALT, VK_SPACE, "Alt+Leertaste"),
    (MOD_CONTROL | MOD_SHIFT, VK_SPACE, "Strg+Umschalt+Leertaste"),
]

# Bekannte Programme -> was gestartet wird (Programmname, URI oder Pfad)
KNOWN_APPS = {
    "notepad": "notepad", "editor": "notepad",
    "calc": "calc", "rechner": "calc",
    "explorer": "explorer",
    "paint": "mspaint",
    "cmd": "cmd", "powershell": "powershell",
    "settings": "ms-settings:", "einstellungen": "ms-settings:",
    "taskmgr": "taskmgr", "task-manager": "taskmgr",
    "edge": "msedge", "chrome": "chrome", "firefox": "firefox",
    "spotify": "spotify:", "discord": "discord:", "steam": "steam://open/main",
    "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
    "vscode": "code",
}

FOLDERS = {
    "desktop": "~/Desktop", "downloads": "~/Downloads", "documents": "~/Documents",
    "pictures": "~/Pictures", "music": "~/Music", "videos": "~/Videos",
}


# ---------------------------------------------------------------- Startmenü-Apps
def find_start_menu_apps():
    dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]
    junk = re.compile(r"uninstall|deinstall|readme|help|hilfe|handbuch|manual|documentation|"
                      r"release notes|tutorial|reference|website", re.I)
    apps = {}
    for d in dirs:
        for path in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            name = os.path.splitext(os.path.basename(path))[0]
            if not junk.search(name):
                apps.setdefault(name, path)
    return apps


START_MENU_APPS = find_start_menu_apps()

def build_prompt(escalated):
    """System-Prompt für Haiku (mit escalate) oder für den eskalierten Lauf (ohne escalate)."""
    if escalated:
        answer_rule = ("Antwort auf Fragen, Rechnungen, Übersetzungen, Erklärungen, Code. Du wurdest "
                       "gewählt, weil die Aufgabe anspruchsvoll ist: antworte gründlich, aber kompakt "
                       "(höchstens ca. 15 Zeilen). Nur reiner Text, kein Markdown (keine **, #, ```); "
                       "Absätze und Aufzählungen mit Zeilenumbruch und „- “, Code eingerückt.")
    else:
        answer_rule = "Kurze Antwort (max. 3 Sätze) auf Fragen, Rechnungen, Übersetzungen, Erklärungen."
    prompt = f"""Du bist der Assistent in einer Windows-Suchleiste. Der Nutzer tippt einen Befehl oder eine Frage.
Antworte AUSSCHLIESSLICH mit einem JSON-Objekt, ohne Markdown, ohne Erklärung:
{{"actions":[ ... ]}}

Mögliche Aktionen:
- {{"type":"open_url","url":"https://..."}}  Website öffnen. Nutze direkte Such-URLs, z. B.
  https://www.youtube.com/results?search_query=..., https://www.google.com/search?q=...,
  https://de.wikipedia.org/wiki/..., https://www.google.com/maps/search/..., https://www.amazon.de/s?k=...
- {{"type":"open_app","name":"..."}}  Programm starten. name ist entweder einer von
  {", ".join(sorted(set(KNOWN_APPS)))}
  oder exakt einer dieser installierten Programmnamen: {"; ".join(sorted(START_MENU_APPS))}
- {{"type":"open_folder","path":"..."}}  Ordner öffnen: {", ".join(FOLDERS)} oder ein absoluter Windows-Pfad.
- {{"type":"answer","text":"..."}}  {answer_rule}"""
    if not escalated:
        prompt += f"""
- {{"type":"escalate","model":"sonnet|opus","effort":"{"|".join(EFFORTS)}","reason":"kurz"}}
  Aufgabe an ein stärkeres Modell abgeben, das sie dann komplett neu bearbeitet.

Wann escalate (dann NUR diese eine Aktion zurückgeben):
- mehrstufiges Nachdenken, Vergleiche und Abwägungen, Code schreiben oder erklären,
  längere Erklärungen, Mathematik über einfaches Rechnen hinaus, Fakten, bei denen du
  unsicher bist, oder alles, wofür eine Antwort in 3 Sätzen schlecht wäre.
- der Nutzer verlangt es ausdrücklich („gründlich“, „ausführlich“, „denk genau nach“, „ultra“).
Wann NICHT escalate (selbst erledigen, schneller Weg):
- Websites, Programme oder Ordner öffnen, Suchen starten, einfache Fakten,
  einfache Rechnungen, kurze Übersetzungen, Einheiten umrechnen.
Modell und Stufe wählst du selbst nach Schwierigkeit:
- sonnet + low/medium: mittel (kurze Erklärung mit etwas Nachdenken, Textentwurf, kleines Code-Snippet)
- sonnet + high: Code, mehrstufige Logik, Vergleiche, Rechenaufgaben mit mehreren Schritten
- opus + high/xhigh: schwierige Analyse, komplexer Code oder Algorithmen, knifflige Mathematik
- opus + max: nur sehr schwere Aufgaben (Beweise, komplexe Architektur) oder wenn „ultra“ verlangt wird"""
    prompt += """

Mehrere Aktionen in einer Liste sind erlaubt (z. B. zwei Websites öffnen).
Wenn unklar ist, was gemeint ist, mach eine Google-Suche. Antworte auf Deutsch."""
    return prompt


SYSTEM_PROMPT = build_prompt(escalated=False)
SYSTEM_PROMPT_DEEP = build_prompt(escalated=True)


# ---------------------------------------------------------------- Claude
def find_claude():
    found = shutil.which("claude")
    if found:
        return found
    fallback = os.path.expanduser(r"~\.local\bin\claude.exe")
    return fallback if os.path.exists(fallback) else None


CLAUDE = find_claude()
PROMPT_FILE = os.path.join(tempfile.gettempdir(), "claude_leiste_prompt.txt")
PROMPT_FILE_DEEP = os.path.join(tempfile.gettempdir(), "claude_leiste_prompt_deep.txt")
for _path, _prompt in ((PROMPT_FILE, SYSTEM_PROMPT), (PROMPT_FILE_DEEP, SYSTEM_PROMPT_DEEP)):
    with open(_path, "w", encoding="utf-8") as f:
        f.write(_prompt)

# Wörter -> gültige Werte (für Präfixe und zum Absichern von Haikus Angaben)
MODEL_WORDS = {"haiku": "haiku", "sonnet": "sonnet", "opus": "opus"}
EFFORT_WORDS = {
    "low": "low", "niedrig": "low", "schnell": "low",
    "medium": "medium", "mittel": "medium", "normal": "medium",
    "high": "high", "hoch": "high",
    "xhigh": "xhigh", "x-high": "xhigh", "extra": "xhigh", "sehrhoch": "xhigh",
    "max": "max", "maximum": "max", "ultra": "max",
}


def model_label(model, effort=None):
    """z. B. "Opus · max" oder "Haiku"."""
    return model.capitalize() + (f" · {effort}" if effort else "")


def clamp(model, effort):
    """Haikus/Präfix-Angaben auf gültige CLI-Werte bringen. "ultra" -> Opus + max."""
    model = str(model or "").strip().lower()
    effort = str(effort or "").strip().lower()
    if model == "ultra" or effort == "ultra":
        return "opus", "max"
    model = MODEL_WORDS.get(model, ESCALATE_MODEL)
    effort = EFFORT_WORDS.get(effort, ESCALATE_EFFORT)
    return model, effort


def parse_overrides(text):
    """Liest Präfixe wie "!opus !max" vom Textanfang. Gibt (model, effort, rest) zurück,
    model/effort sind None, wenn nicht angegeben."""
    model = effort = None
    words = text.split()
    while words and words[0].startswith("!"):
        word = words[0][1:].lower()
        if word == "ultra":
            model, effort = model or "opus", "max"
        elif word in MODEL_WORDS:
            model = MODEL_WORDS[word]
        elif word in EFFORT_WORDS:
            effort = EFFORT_WORDS[word]
        else:
            break  # unbekanntes "!wort" gehört zum Text
        words.pop(0)
    return model, effort, " ".join(words)


def call_claude(text, model, effort=None, deep=False):
    """Ein CLI-Aufruf. deep=True: Prompt ohne escalate, längere Antworten."""
    if not CLAUDE:
        raise RuntimeError("Claude Code (claude.exe) wurde nicht gefunden.")
    cmd = [CLAUDE, "-p", "--model", model, "--tools", "", "--no-session-persistence",
           "--setting-sources", "", "--system-prompt-file", PROMPT_FILE_DEEP if deep else PROMPT_FILE]
    if effort and model != "haiku":  # Haiku bleibt ohne Denkstufe (schneller Weg)
        cmd += ["--effort", effort]
    if not deep:
        timeout = TIMEOUT_FAST
    else:
        timeout = TIMEOUT_DEEP if effort in ("high", "xhigh", "max") else TIMEOUT_ESCALATED
    try:
        result = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding="utf-8",
                                timeout=timeout, cwd=tempfile.gettempdir(),
                                creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{model_label(model, effort)} hat nach {timeout} s nicht geantwortet.")
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "Claude-Fehler").strip()[:300])
    out = result.stdout.strip()
    match = re.search(r"\{.*\}", out, re.S)
    try:
        return json.loads(match.group(0))["actions"]
    except (AttributeError, ValueError, KeyError):
        return [{"type": "answer", "text": out}]


def ask_claude(text, on_status=None):
    """Haiku bewertet zuerst; bei "escalate" läuft derselbe Text noch einmal mit dem gewählten
    Modell/Effort. Präfixe (!opus, !max, ...) überspringen Haiku. Gibt (actions, label) zurück.
    on_status(text) meldet, welches Modell gerade nachdenkt."""
    status = on_status or (lambda _s: None)
    model, effort, rest = parse_overrides(text)
    if model or effort:  # manuell festgelegt
        if model == "haiku":
            effort = None
        else:
            model, effort = clamp(model, effort)
        status(f"{model_label(model, effort)} denkt nach")
        actions = call_claude(rest or text, model, effort, deep=True)
        return [a for a in actions if a.get("type") != "escalate"], model_label(model, effort)

    status(f"{model_label(MODEL)} denkt nach")
    actions = call_claude(text, MODEL)
    escalation = next((a for a in actions if a.get("type") == "escalate"), None)
    if not escalation:
        return actions, model_label(MODEL)
    # Andere Aktionen neben escalate werden ignoriert: das stärkere Modell entscheidet neu.
    model, effort = clamp(escalation.get("model"), escalation.get("effort"))
    if model == "haiku":  # an sich selbst abgeben ergibt keinen Sinn
        model = ESCALATE_MODEL
    status(f"→ {model_label(model, effort)} denkt nach")
    actions = call_claude(text, model, effort, deep=True)
    return [a for a in actions if a.get("type") != "escalate"], model_label(model, effort)


# ---------------------------------------------------------------- Aktionen
def launch(target):
    try:
        os.startfile(target)
    except OSError:
        subprocess.Popen(["cmd", "/c", "start", "", target], creationflags=CREATE_NO_WINDOW)


def open_app(name):
    key = name.strip().lower()
    if key in KNOWN_APPS:
        return launch(KNOWN_APPS[key])
    if name in START_MENU_APPS:
        return launch(START_MENU_APPS[name])
    for app, path in START_MENU_APPS.items():
        if key in app.lower():
            return launch(path)
    launch(name)


def run_actions(actions):
    """Führt die Aktionen aus und gibt den anzuzeigenden Text zurück (oder None)."""
    texts = []
    for action in actions:
        kind = action.get("type")
        try:
            if kind == "open_url":
                url = action["url"]
                if urllib.parse.urlparse(url).scheme in ("http", "https"):
                    webbrowser.open(url)
            elif kind == "open_app":
                open_app(action["name"])
            elif kind == "open_folder":
                path = action["path"]
                launch(os.path.expanduser(FOLDERS.get(path.lower(), path)))
            elif kind == "answer":
                texts.append(action["text"])
        except Exception as e:  # eine fehlgeschlagene Aktion soll die anderen nicht stoppen
            texts.append(f"Konnte {kind} nicht ausführen: {e}")
    return "\n\n".join(texts) or None


# ---------------------------------------------------------------- Oberfläche
def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kw)


class Leiste:
    def __init__(self):
        self.events = queue.Queue()
        self.busy = False
        self.history = []
        self.history_pos = 0
        self.thinking = ""  # z. B. "Haiku denkt nach"
        self.full_answer = ""  # ungekürzte Antwort zum Kopieren
        self.status_space = 98  # Platz rechts in der Leiste für den Status (Pixel)

        self.root = tk.Tk()
        self.root.title("Claude-Leiste")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", TRANSPARENT)
        self.root.configure(bg=TRANSPARENT)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=BAR_HEIGHT, bg=TRANSPARENT,
                                highlightthickness=0, bd=0)
        self.canvas.pack()

        self.star = tk.Label(self.root, text="✳", font=("Segoe UI Symbol", 20), fg=ACCENT, bg=BG)
        self.star.bind("<Button-3>", lambda e: self.quit())
        self.entry = tk.Entry(self.root, font=FONT, bg=BG, fg=FG, insertbackground=FG,
                              relief="flat", bd=0, highlightthickness=0)
        self.status = tk.Label(self.root, text="", font=ANSWER_FONT, fg=MUTED, bg=BG)
        self.status_font = tkfont.Font(root=self.root, font=ANSWER_FONT)
        self.answer = tk.Label(self.root, text="", font=ANSWER_FONT, fg=FG, bg=BG, justify="left",
                               anchor="nw", wraplength=WIDTH - 60, cursor="hand2")
        self.answer.bind("<Button-1>", self.copy_answer)

        self.entry.bind("<Return>", self.submit)
        self.entry.bind("<Escape>", lambda e: self.hide())
        self.entry.bind("<Up>", lambda e: self.browse_history(-1))
        self.entry.bind("<Down>", lambda e: self.browse_history(1))
        self.root.bind("<FocusOut>", lambda e: self.root.after(150, self.hide_if_unfocused))

        self.layout(None)
        self.root.withdraw()
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        self.root.after(50, self.poll)

    # -- Aufbau
    def layout(self, answer_text):
        self.canvas.delete("all")
        height = BAR_HEIGHT
        if answer_text:
            self.full_answer = answer_text
            self.answer.config(text=answer_text)
            self.answer.update_idletasks()
            if self.answer.winfo_reqheight() > ANSWER_MAX_HEIGHT:
                self.fit_answer(answer_text)
            height = BAR_HEIGHT + self.answer.winfo_reqheight() + 18
        self.canvas.config(height=height)
        round_rect(self.canvas, 1, 1, WIDTH - 1, height - 1, 28, fill=BG, outline="#3a3a42")
        self.canvas.create_window(30, BAR_HEIGHT // 2, window=self.star)
        self.entry_win = self.canvas.create_window(58, BAR_HEIGHT // 2, window=self.entry,
                                                   anchor="w", height=34,
                                                   width=WIDTH - 82 - self.status_space)
        self.canvas.create_window(WIDTH - 24, BAR_HEIGHT // 2, window=self.status, anchor="e")
        if answer_text:
            self.canvas.create_line(24, BAR_HEIGHT, WIDTH - 24, BAR_HEIGHT, fill="#34343b")
            self.canvas.create_window(30, BAR_HEIGHT + 8, window=self.answer, anchor="nw")

    def fit_answer(self, text):
        """Kürzt die angezeigte Antwort auf ANSWER_MAX_HEIGHT (Binärsuche über die Länge)."""
        suffix = "\n… (gekürzt – Klick kopiert den ganzen Text)"
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            self.answer.config(text=text[:mid].rstrip() + suffix)
            self.answer.update_idletasks()
            if self.answer.winfo_reqheight() <= ANSWER_MAX_HEIGHT:
                lo = mid
            else:
                hi = mid - 1
        cut = max(text.rfind(" ", 0, lo), text.rfind("\n", 0, lo))
        if cut > lo - 40:  # nicht mitten im Wort abschneiden
            lo = cut
        self.answer.config(text=text[:lo].rstrip() + suffix)

    def set_status(self, text, reserve=None):
        """Status rechts setzen; das Eingabefeld macht bei langem Status Platz.
        reserve = breitester Text, für den Platz reserviert wird (gegen Zappeln)."""
        self.status.config(text=text)
        self.status_space = max(98, self.status_font.measure(reserve or text) + 12)
        self.canvas.itemconfig(self.entry_win, width=WIDTH - 82 - self.status_space)

    def place(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - WIDTH) // 2}+{int(sh * 0.28)}")

    # -- Anzeigen / Verstecken
    def show(self):
        self.set_status("")
        self.layout(None)
        self.place()
        self.root.deiconify()
        self.root.lift()
        self.force_focus()
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def force_focus(self):
        self.root.update_idletasks()
        hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        fg_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        my_thread = kernel32.GetCurrentThreadId()
        user32.AttachThreadInput(fg_thread, my_thread, True)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        user32.AttachThreadInput(fg_thread, my_thread, False)
        self.root.focus_force()

    def hide(self):
        self.root.withdraw()

    def hide_if_unfocused(self):
        if self.root.focus_get() is None and not self.busy:
            self.hide()

    def toggle(self):
        if self.root.state() == "withdrawn":
            self.show()
        else:
            self.hide()

    # -- Eingabe
    def submit(self, _event=None):
        text = self.entry.get().strip()
        if not text or self.busy:
            return
        if text.lower() in ("beenden", "exit", "quit"):
            return self.quit()
        self.history.append(text)
        self.history_pos = len(self.history)
        self.busy = True
        self.thinking = "denkt nach"
        self.layout(None)
        self.animate(0)
        threading.Thread(target=self.work, args=(text,), daemon=True).start()

    def work(self, text):
        try:
            actions, label = ask_claude(text, on_status=lambda s: self.events.put(("status", s)))
            self.events.put(("done", (run_actions(actions), label)))
        except Exception as e:
            self.events.put(("done", (f"Fehler: {e}", None)))

    def finish(self, result):
        text, label = result
        self.busy = False
        self.set_status("")
        self.star.config(fg=ACCENT)
        if text:
            if self.root.state() == "withdrawn":  # lange Läufe: Antwort trotzdem zeigen
                self.place()
                self.root.deiconify()
                self.root.lift()
            self.layout(text)
            self.set_status(label or "")  # dezenter Hinweis, welches Modell geantwortet hat
            self.entry.select_range(0, "end")
        else:
            self.entry.delete(0, "end")
            self.hide()

    def animate(self, step):
        if not self.busy:
            return
        self.set_status(self.thinking + "." * (step % 4), reserve=self.thinking + "...")
        self.star.config(fg=ACCENT if step % 2 == 0 else "#f0b49c")
        self.root.after(350, self.animate, step + 1)

    def browse_history(self, direction):
        if not self.history:
            return
        self.history_pos = max(0, min(len(self.history), self.history_pos + direction))
        self.entry.delete(0, "end")
        if self.history_pos < len(self.history):
            self.entry.insert(0, self.history[self.history_pos])

    def copy_answer(self, _event=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.full_answer or self.answer.cget("text"))
        self.set_status("kopiert ✓")

    # -- Hotkey
    def hotkey_loop(self):
        for mod, vk, label in HOTKEYS:
            if user32.RegisterHotKey(None, 1, mod | MOD_NOREPEAT, vk):
                self.events.put(("ready", label))
                break
        else:
            self.events.put(("ready", None))
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                self.events.put(("toggle", None))

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "toggle":
                    self.toggle()
                elif kind == "status":
                    self.thinking = value
                elif kind == "done":
                    self.finish(value)
                elif kind == "ready":
                    self.show()
                    if value:
                        self.layout(f"Claude-Leiste läuft. Öffnen/Schließen mit {value}. "
                                    "Beenden: „beenden“ eintippen oder Rechtsklick auf ✳.")
                    else:
                        self.layout("Kein Tastenkürzel frei. Die Leiste bleibt offen, "
                                    "„beenden“ schließt sie.")
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def quit(self):
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # Nur eine Instanz gleichzeitig
    kernel32.CreateMutexW(None, False, "ClaudeLeisteSingleInstance")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)
    Leiste().run()
