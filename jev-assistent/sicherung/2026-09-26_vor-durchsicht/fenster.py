"""fenster.py - offene Fenster auflisten, in den Vordergrund holen, schliessen.

Damit wirkt der Assistent in JEDEM Programm, nicht nur in den in config.json
eingetragenen: er sucht das Fenster, holt es nach vorne, danach tippt
tastatur.py hinein.

  python fenster.py                 offene Fenster zeigen
  python fenster.py "discord"       Fenster mit diesem Namen nach vorne holen
"""
import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwm = ctypes.WinDLL("dwmapi", use_last_error=True)

SW_RESTORE, SW_MINIMIZE, SW_MAXIMIZE = 9, 6, 3
DWMWA_CLOAKED = 14
WM_CLOSE = 0x0010

user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
kernel32.OpenProcess.restype = wintypes.HANDLE
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _titel(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if not n:
        return ""
    puffer = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, puffer, n + 1)
    return puffer.value


def _versteckt(hwnd):
    """UWP-Geisterfenster erkennen (sichtbar gemeldet, aber vom System verdeckt)."""
    wert = wintypes.DWORD()
    if dwm.DwmGetWindowAttribute(wintypes.HWND(hwnd), DWMWA_CLOAKED,
                                 ctypes.byref(wert), ctypes.sizeof(wert)) == 0:
        return bool(wert.value)
    return False


def _prozess(hwnd):
    return pfad(hwnd).rsplit("\\", 1)[-1]


def pfad(hwnd):
    """Voller Pfad der Programmdatei hinter einem Fenster ("" wenn nicht lesbar)."""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        puffer = ctypes.create_unicode_buffer(260)
        groesse = wintypes.DWORD(260)
        if kernel32.QueryFullProcessImageNameW(h, 0, puffer, ctypes.byref(groesse)):
            return puffer.value
        return ""
    finally:
        kernel32.CloseHandle(h)


def liste():
    """-> [{'hwnd': int, 'titel': str, 'prozess': str}] der echten Fenster."""
    gefunden = []

    def dazu(hwnd, _):
        if user32.IsWindowVisible(hwnd) and not _versteckt(hwnd):
            t = _titel(hwnd)
            if t and t not in ("Program Manager", "Windows-Eingabeerfahrung"):
                gefunden.append({"hwnd": hwnd, "titel": t, "prozess": _prozess(hwnd)})
        return True

    user32.EnumWindows(WNDENUMPROC(dazu), 0)
    return gefunden


def aktives():
    hwnd = user32.GetForegroundWindow()
    return {"hwnd": hwnd, "titel": _titel(hwnd), "prozess": _prozess(hwnd)}


def suche(name):
    """Fenster nach Name oder Prozess finden; bester Treffer zuerst."""
    n = (name or "").strip().lower()
    if not n:
        return None
    treffer = []
    for w in liste():
        t, p = w["titel"].lower(), w["prozess"].lower()
        if n in t or n in p:
            # genauer Anfang schlaegt Fund irgendwo in der Mitte
            treffer.append((t.startswith(n) or p.startswith(n), len(t), w))
    if not treffer:
        return None
    treffer.sort(key=lambda x: (not x[0], x[1]))
    return treffer[0][2]


def nach_vorne(hwnd):
    """Fenster in den Vordergrund holen. -> True bei Erfolg."""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    # Windows blockiert SetForegroundWindow aus Hintergrundprozessen; ein Alt-Tipp hebt das auf
    import tastatur
    tastatur.druecke("alt")
    user32.SetForegroundWindow(hwnd)
    for _ in range(10):
        time.sleep(0.05)
        if user32.GetForegroundWindow() == hwnd:
            return True
    return user32.GetForegroundWindow() == hwnd


def zeigen(name):
    """Fenster suchen und nach vorne holen. -> gefundenes Fenster oder None."""
    w = suche(name)
    if w and nach_vorne(w["hwnd"]):
        return w
    return w if w else None


def schliessen(hwnd):
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1:
        w = zeigen(" ".join(sys.argv[1:]))
        print(f"nach vorne: {w['titel']} ({w['prozess']})" if w else "kein Fenster gefunden")
        return
    for w in liste():
        print(f"  {w['prozess']:24} {w['titel'][:70]}")


if __name__ == "__main__":
    main()
