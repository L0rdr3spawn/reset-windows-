"""autostart.py - den Assistenten mit Windows starten lassen (oder wieder nicht).

Legt eine Verknuepfung im Autostart-Ordner des Benutzers an, die
pythonw.exe (ohne Konsolenfenster) mit jev_assistent.py startet.
Keine Administratorrechte, keine Registry, jederzeit sichtbar unter
  Win+R -> shell:startup

  python autostart.py status
  python autostart.py ein
  python autostart.py aus
"""
import os
import subprocess
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent
SKRIPT = BASIS / "jev_assistent.py"
NAME = "Jev-Assistent.lnk"
AUTOSTART = Path(os.environ["APPDATA"]) / r"Microsoft\Windows\Start Menu\Programs\Startup"
VERKNUEPFUNG = AUTOSTART / NAME
# Hier merkt sich Windows, ob ein Autostart-Eintrag in "Autostart-Apps" / Task-Manager abgeschaltet ist.
# Die Verknüpfung bleibt dabei liegen - Windows ignoriert sie nur still (so geschehen am 29.09.2026).
FREIGABE = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"


def pythonw():
    """pythonw.exe neben dem laufenden Python (startet ohne Konsolenfenster)."""
    p = Path(sys.executable).with_name("pythonw.exe")
    return p if p.exists() else Path(sys.executable)


def _powershell(befehl):
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", befehl],
                          capture_output=True, text=True)


def von_windows_gesperrt():
    """True, wenn der Eintrag in den Windows-Autostart-Apps ausgeschaltet ist."""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, FREIGABE) as k:
            wert = winreg.QueryValueEx(k, NAME)[0]
    except OSError:
        return False
    return bool(wert) and wert[0] % 2 == 1      # 02/06 = an, 03/07 = aus


def freigeben():
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, FREIGABE) as k:
        winreg.SetValueEx(k, NAME, 0, winreg.REG_BINARY, bytes([2] + [0] * 11))


def ein():
    if VERKNUEPFUNG.exists() and von_windows_gesperrt():
        freigeben()
        return f"Autostart war in Windows ausgeschaltet - wieder eingeschaltet: {VERKNUEPFUNG}"
    ziel = pythonw()
    ps = (f"$w = New-Object -ComObject WScript.Shell; "
          f"$l = $w.CreateShortcut('{VERKNUEPFUNG}'); "
          f"$l.TargetPath = '{ziel}'; "
          f"$l.Arguments = '\"{SKRIPT}\"'; "
          f"$l.WorkingDirectory = '{BASIS}'; "
          f"$l.Description = 'Jev-Assistent (Sprachsteuerung)'; "
          f"$l.Save()")
    r = _powershell(ps)
    if r.returncode != 0 or not VERKNUEPFUNG.exists():
        return f"Autostart konnte nicht eingerichtet werden: {(r.stderr or r.stdout).strip()[:200]}"
    if von_windows_gesperrt():
        freigeben()
    return f"Autostart ein: {VERKNUEPFUNG}"


def aus():
    if VERKNUEPFUNG.exists():
        VERKNUEPFUNG.unlink()
        return "Autostart aus."
    return "Autostart war nicht eingerichtet."


def status():
    if not VERKNUEPFUNG.exists():
        return "Autostart: aus"
    r = _powershell(f"$w = New-Object -ComObject WScript.Shell; "
                    f"$l = $w.CreateShortcut('{VERKNUEPFUNG}'); "
                    f"\"$($l.TargetPath) $($l.Arguments)\"")
    if von_windows_gesperrt():
        return "Autostart: AUS - in den Windows-Autostart-Apps abgeschaltet (python autostart.py ein)"
    return f"Autostart: ein -> {r.stdout.strip()}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = (sys.argv[1:] or ["status"])[0].lower()
    print({"ein": ein, "an": ein, "aus": aus, "status": status}.get(a, status)())


if __name__ == "__main__":
    main()
