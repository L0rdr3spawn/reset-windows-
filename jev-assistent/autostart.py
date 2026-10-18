"""autostart.py - den Assistenten mit Windows starten lassen (oder wieder nicht).

Trägt Jeff.exe (kleiner Starter, siehe launcher\\JeffLauncher.cs) unter
  HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
ein - genau wie Discord, Spotify, Steam. Keine Administratorrechte.
Dadurch steht der Assistent mit seinem Namen (aus config.json, "name") in
  Windows-Einstellungen -> Apps -> Autostart   und   Task-Manager -> Autostart-Apps
und lässt sich dort, hier oder im Einstellungsfenster ein- und ausschalten.

  python autostart.py status
  python autostart.py ein
  python autostart.py aus

Früher lag stattdessen Jev-Assistent.lnk im Autostart-Ordner (shell:startup) und erschien
dort nur als "pythonw". ein() und aus() räumen diese Verknüpfung weg, damit Jeff nie doppelt startet.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent
SKRIPT = BASIS / "jev_assistent.py"
KONFIG = BASIS / "config.json"
EXE = BASIS / "Jeff.exe"
LAUNCHER = BASIS / "launcher"
QUELLE = LAUNCHER / "JeffLauncher.cs"
VERSIONSINFO = LAUNCHER / "Versionsinfo.cs"        # wird bei jedem ein() neu geschrieben
SYMBOL = LAUNCHER / "jeff.ico"
CSC = Path(os.environ.get("WINDIR", r"C:\Windows")) / r"Microsoft.NET\Framework64\v4.0.30319\csc.exe"
VERSION = "1.0.0.0"

RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
# Hier merkt sich Windows, ob ein Autostart-Eintrag in "Autostart-Apps" / Task-Manager abgeschaltet ist.
# Der Eintrag selbst bleibt dabei stehen - Windows ignoriert ihn nur still (so geschehen am 29.09.2026).
FREIGABE = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"

# Alter Weg (bis 04.10.2026): Verknüpfung im Autostart-Ordner
ALT_NAME = "Jev-Assistent.lnk"
ALTE_VERKNUEPFUNG = Path(os.environ["APPDATA"]) / r"Microsoft\Windows\Start Menu\Programs\Startup" / ALT_NAME
ALT_FREIGABE = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"

OHNE_FENSTER = 0x08000000      # CREATE_NO_WINDOW: kein Konsolenblitzen, wenn das Einstellungsfenster ein() ruft


def name():
    """Name des Assistenten aus config.json (Standard: Jeff)."""
    try:
        n = json.loads(KONFIG.read_text(encoding="utf-8-sig")).get("name", "Jeff")
    except (OSError, ValueError):
        return "Jeff"
    n = str(n or "").strip()
    return n or "Jeff"


def befehl():
    return f'"{EXE}"'


# --- Registry ---------------------------------------------------------------

def _werte(schluessel):
    """Alle Werte eines HKCU-Schlüssels als {Name: Daten}."""
    import winreg
    werte = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, schluessel) as k:
            i = 0
            while True:
                try:
                    n, d, _ = winreg.EnumValue(k, i)
                except OSError:
                    break
                werte[n] = d
                i += 1
    except OSError:
        pass
    return werte


def _loeschen(schluessel, wert):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, schluessel, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, wert)
        return True
    except OSError:
        return False


def _gesperrt(schluessel, wert):
    """True, wenn der Eintrag in den Windows-Autostart-Apps ausgeschaltet ist."""
    d = _werte(schluessel).get(wert)
    return isinstance(d, bytes) and bool(d) and d[0] % 2 == 1      # 02/06 = an, 03/07 = aus


def eintraege():
    """Namen der Run-Werte, die Jeff.exe starten (nach einer Umbenennung evtl. noch der alte Name)."""
    ziel = str(EXE).lower()
    return [n for n, d in _werte(RUN).items() if isinstance(d, str) and ziel in d.lower()]


def von_windows_gesperrt():
    """True, wenn Jeff eingetragen, aber in den Windows-Autostart-Apps ausgeschaltet ist."""
    e = eintraege()
    return bool(e) and all(_gesperrt(FREIGABE, n) for n in e)


def ist_an():
    """Startet Jeff mit Windows? (Eintrag vorhanden und nicht in Windows abgeschaltet)"""
    return any(not _gesperrt(FREIGABE, n) for n in eintraege())


def _alten_weg_entfernen():
    """Verknüpfung aus dem Autostart-Ordner (alter Weg) wegräumen. -> True, wenn etwas weg ist"""
    weg = False
    if ALTE_VERKNUEPFUNG.exists():
        ALTE_VERKNUEPFUNG.unlink()
        weg = True
    return _loeschen(ALT_FREIGABE, ALT_NAME) or weg


# --- Starter Jeff.exe -------------------------------------------------------

def _cs_text(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def starter_bauen():
    """Jeff.exe mit dem aktuellen Namen neu übersetzen. -> Fehlertext oder ''"""
    if not CSC.exists():
        return f"C#-Compiler fehlt: {CSC}"
    n = _cs_text(name())
    VERSIONSINFO.write_text(
        "// Automatisch erzeugt von autostart.py - Änderungen hier gehen beim nächsten 'ein' verloren.\n"
        "using System.Reflection;\n\n"
        f'[assembly: AssemblyTitle("{n} – Sprachassistent")]\n'
        f'[assembly: AssemblyDescription("{n} – Sprachassistent")]\n'
        f'[assembly: AssemblyProduct("{n}")]\n'
        '[assembly: AssemblyCompany("Jev-Assistent")]\n'
        '[assembly: AssemblyCopyright("Jev-Assistent")]\n'
        f'[assembly: AssemblyVersion("{VERSION}")]\n'
        f'[assembly: AssemblyFileVersion("{VERSION}")]\n',
        encoding="utf-8-sig")
    neu = EXE.with_suffix(".neu.exe")
    aufruf = [str(CSC), "/nologo", "/target:winexe", "/optimize+", "/codepage:65001", f"/out:{neu}",
              str(QUELLE), str(VERSIONSINFO)]
    if SYMBOL.exists():
        aufruf.insert(-2, f"/win32icon:{SYMBOL}")
    r = subprocess.run(aufruf, capture_output=True, text=True, encoding="oem", errors="replace",
                       creationflags=OHNE_FENSTER)
    if r.returncode != 0 or not neu.exists():
        neu.unlink(missing_ok=True)
        meldung = " ".join(z.strip() for z in (r.stdout + r.stderr).splitlines() if "error" in z.lower())
        return f"Jeff.exe konnte nicht übersetzt werden: {(meldung or r.stdout or r.stderr).strip()[:300]}"
    try:
        os.replace(neu, EXE)
    except OSError as e:
        neu.unlink(missing_ok=True)
        if not EXE.exists():
            return f"Jeff.exe konnte nicht geschrieben werden: {e}"
        return ""       # alte Jeff.exe ist gerade gesperrt - sie startet trotzdem, nur evtl. mit altem Namen
    return ""


# --- Öffentliche Schnittstelle (auch vom Einstellungsfenster benutzt) ---------

def ein():
    import winreg
    fehler = starter_bauen()
    if not EXE.exists():
        return f"Autostart konnte nicht eingerichtet werden. {fehler}"
    n = name()
    for alt in eintraege():                     # alter Name nach Umbenennung
        if alt != n:
            _loeschen(RUN, alt)
            _loeschen(FREIGABE, alt)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN) as k:
        winreg.SetValueEx(k, n, 0, winreg.REG_SZ, befehl())
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, FREIGABE) as k:
        winreg.SetValueEx(k, n, 0, winreg.REG_BINARY, bytes([2] + [0] * 11))
    _alten_weg_entfernen()
    text = f"Autostart ein: {n} startet mit Windows ({EXE.name})."
    return f"{text} Achtung: {fehler}" if fehler else text


def aus():
    weg = False
    for n in set(eintraege()) | {name()}:
        weg = _loeschen(RUN, n) or weg
        _loeschen(FREIGABE, n)
    weg = _alten_weg_entfernen() or weg
    return "Autostart aus." if weg else "Autostart war nicht eingerichtet."


def status():
    e = eintraege()
    if not e:
        if ALTE_VERKNUEPFUNG.exists():
            return ("Autostart: alter Eintrag im Autostart-Ordner (erscheint als \"pythonw\") - "
                    "python autostart.py ein stellt um")
        return "Autostart: aus"
    if not ist_an():
        return "Autostart: AUS - in den Windows-Autostart-Apps abgeschaltet (python autostart.py ein)"
    text = f"Autostart: ein -> {', '.join(e)} = {befehl()}"
    if name() not in e:
        text += f" (Name in config.json ist jetzt \"{name()}\" - python autostart.py ein aktualisiert)"
    if not EXE.exists():
        text += " - Jeff.exe fehlt! (python autostart.py ein)"
    return text


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = (sys.argv[1:] or ["status"])[0].lower()
    print({"ein": ein, "an": ein, "aus": aus, "status": status}.get(a, status)())


if __name__ == "__main__":
    main()
