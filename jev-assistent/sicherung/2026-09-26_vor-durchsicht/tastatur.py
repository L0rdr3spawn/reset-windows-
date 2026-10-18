"""Tastatureingaben per SendInput: Tastenkürzel, Medientasten und Unicode-Text."""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

TASTEN = {
    "ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
    "enter": 0x0D, "backspace": 0x08, "esc": 0x1B, "tab": 0x09, "space": 0x20,
    "lauter": 0xAF, "leiser": 0xAE, "stumm": 0xAD,
    "play_pause": 0xB3, "naechstes": 0xB0, "vorheriges": 0xB1,
    **{f"f{n}": 0x6F + n for n in range(1, 13)},
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _EINGABE(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _EINGABE)]


def _senden(eingaben):
    feld = (INPUT * len(eingaben))(*eingaben)
    user32.SendInput(len(eingaben), feld, ctypes.sizeof(INPUT))


def _taste(vk=0, scan=0, flags=0):
    return INPUT(type=INPUT_KEYBOARD, u=_EINGABE(ki=KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags)))


def _vk(name):
    name = name.strip().lower()
    if name in TASTEN:
        return TASTEN[name]
    if len(name) == 1 and name.isalnum():
        return ord(name.upper())
    raise ValueError(f"Unbekannte Taste: {name}")


def _scan(vk):
    """Hardware-Scancode zur Taste. WinUI-Programme (Notepad, Einstellungen) ignorieren
    eingespeiste Tasten ohne Scancode - Strg+S/Strg+V kamen dort sonst nicht an."""
    return user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC


def druecke(kombi, anzahl=1):
    """Drückt ein Kürzel wie "ctrl+shift+alt+m" oder eine einzelne Taste wie "lauter"."""
    codes = [_vk(t) for t in kombi.split("+")]
    for _ in range(anzahl):
        runter = [_taste(c, scan=_scan(c)) for c in codes]
        hoch = [_taste(c, scan=_scan(c), flags=KEYEVENTF_KEYUP) for c in reversed(codes)]
        _senden(runter + hoch)
        time.sleep(0.03)


def tippe(text, bloeckchen=16):
    """Tippt beliebigen Text (inkl. Umlaute und Emojis) in das aktive Fenster.

    Die Zeichen gehen gebuendelt raus: einzeln mit 4 ms Pause verschluckten
    Programme wie Notepad Zeichen oder wiederholten das vorige
    ("eins zwei" wurde zu "nnns iiii").
    """
    daten = text.encode("utf-16-le")
    einheiten = [int.from_bytes(daten[i:i + 2], "little") for i in range(0, len(daten), 2)]
    for start in range(0, len(einheiten), bloeckchen):
        eingaben = []
        for einheit in einheiten[start:start + bloeckchen]:
            eingaben.append(_taste(scan=einheit, flags=KEYEVENTF_UNICODE))
            eingaben.append(_taste(scan=einheit, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
        _senden(eingaben)
        time.sleep(0.02)


# --- Zwischenablage: zuverlaessiger Weg, Text in fremde Programme zu bringen ---
# Einzeln getippte Unicode-Zeichen verschlucken moderne Oberflaechen (Notepad/WinUI
# nahm von "test eins zwei drei" nur ein Zeichen an). Einfuegen klappt ueberall.
CF_UNICODETEXT, GMEM_MOVEABLE = 13, 0x0002

# Ohne Prototypen kuerzt ctypes die Handles auf 32 Bit -> Absturz beim Einfuegen
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]


def zwischenablage_lesen():
    if not user32.OpenClipboard(None):
        return None
    try:
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return None
        p = kernel32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p) if p else None
        finally:
            kernel32.GlobalUnlock(h)
    finally:
        user32.CloseClipboard()


def zwischenablage_setzen(text):
    for _ in range(5):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False
    try:
        user32.EmptyClipboard()
        puffer = ctypes.create_unicode_buffer(text)
        groesse = ctypes.sizeof(puffer)
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, groesse)
        p = kernel32.GlobalLock(h)
        ctypes.memmove(p, puffer, groesse)
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_UNICODETEXT, h)
        return True
    finally:
        user32.CloseClipboard()


def einfuegen(text):
    """Text ins aktive Fenster einfuegen; die alte Zwischenablage wird zurueckgelegt."""
    if not text:
        return False
    alt = zwischenablage_lesen()
    if not zwischenablage_setzen(text):
        tippe(text)              # Rueckfall, wenn die Zwischenablage belegt ist
        return True
    time.sleep(0.08)
    druecke("ctrl+v")
    time.sleep(0.3)
    if alt is not None:
        zwischenablage_setzen(alt)
    return True


def vordergrund_prozess():
    """Dateiname des Programms, dessen Fenster gerade vorne ist (z. B. "Discord.exe")."""
    hwnd = user32.GetForegroundWindow()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    try:
        puffer = ctypes.create_unicode_buffer(1024)
        laenge = wintypes.DWORD(1024)
        kernel32.QueryFullProcessImageNameW(handle, 0, puffer, ctypes.byref(laenge))
        return puffer.value.rsplit("\\", 1)[-1]
    finally:
        kernel32.CloseHandle(handle)
