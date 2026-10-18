"""selbsttest.py - prüft alles, was Jeff zum Laufen braucht.

Macht keinen Ton, holt kein Fenster nach vorne und drückt keine Tasten: das
Mikrofon wird nur eine Sekunde lang gelesen, Jev und Claude bekommen je eine
kleine Anfrage. Läuft vor jedem Start über "Jeff starten.cmd".

  python selbsttest.py          alles prüfen
  python selbsttest.py --schnell  ohne Jev-/Claude-Anfrage und ohne Mikrofon

Rückgabewert: 0 = alles gut, 1 = nur Hinweise, 2 = Jeff kann so nicht laufen.
"""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

BASIS = Path(__file__).resolve().parent
OK, HINWEIS, FEHLER = "ok", "hinweis", "fehler"
ZEICHEN = {OK: "[ OK ]", HINWEIS: "[ !! ]", FEHLER: "[FEHL]"}


def pakete():
    noetig = ["numpy", "vosk", "faster_whisper", "sounddevice", "pyttsx3", "typesafe_sdk"]
    fehlt = [m for m in noetig if not importlib.util.find_spec(m)]
    if fehlt:
        return FEHLER, f"fehlen: {', '.join(fehlt)} -> python -m pip install {' '.join(fehlt)}"
    return OK, "alle Python-Pakete da"


def konfiguration():
    try:
        cfg = json.loads((BASIS / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return FEHLER, f"config.json unlesbar: {e}"
    fehlt = [k for k in ("weckwort", "schwellen", "apps", "webseiten", "discord", "spotify") if k not in cfg]
    if fehlt:
        return FEHLER, f"config.json: es fehlt {', '.join(fehlt)}"
    return OK, f"config.json in Ordnung (Weckwort \"{cfg['weckwort']}\", Mindestsicherheit {cfg.get('weckwort_sicherheit', 0.65)})"


def modelle():
    import jev_assistent as j
    if not (j.MODELL / "am").exists():
        return FEHLER, f"Vosk-Modell fehlt: {j.MODELL}"
    whisper = BASIS / "whisper-modelle" / f"models--Systran--faster-whisper-{j.CONFIG['whisper_modell']}"
    if not whisper.exists():
        return HINWEIS, f"Whisper-Modell \"{j.CONFIG['whisper_modell']}\" wird beim ersten Start geladen (Internet nötig)"
    return OK, f"Vosk-Modell und Whisper \"{j.CONFIG['whisper_modell']}\" vorhanden"


def gpu():
    import ctypes
    import jev_assistent as j
    if j.CONFIG.get("whisper_gpu", 1) is None:
        return OK, "Whisper ist auf CPU eingestellt"
    j._cuda_dlls_einbinden()
    try:
        ctypes.WinDLL("cublas64_12.dll")
    except OSError:
        return HINWEIS, ("Whisper läuft auf der CPU (cublas64_12.dll fehlt). Für die RTX 3050: "
                         "\"GPU einrichten.cmd\" ausführen - ca. 500 MB, nicht während eines Spiels")
    return OK, "cuBLAS gefunden, Whisper kann auf der RTX 3050 laufen"


def mikrofon():
    import numpy as np
    import sounddevice as sd
    try:
        geraet = sd.query_devices(kind="input")
        aufnahme = sd.rec(16000, samplerate=16000, channels=1, dtype="int16")
        sd.wait()
    except Exception as e:  # noqa: BLE001
        return FEHLER, f"kein Mikrofon nutzbar: {e}"
    pegel = int(np.abs(aufnahme).max())
    name = geraet["name"].strip()
    if pegel == 0:
        return HINWEIS, f"{name}: liefert nur Stille (stummgeschaltet oder falsches Standardgerät?)"
    return OK, f"{name}: liefert Ton (Spitze {pegel})"


def jev():
    import jev_assistent as j
    if not j.api_key():
        return FEHLER, "TYPESAFE_API_KEY ist nicht gesetzt"
    try:
        from typesafe_sdk import Choice, TypeSafeClient
        start = time.monotonic()
        antwort = TypeSafeClient(api_key=j.api_key()).system_one(
            state={"befehl": "wie spät ist es"},
            questions={"absicht": Choice(instructions={"question": "Was will die Person?"},
                                         criteria={"uhrzeit": "Uhrzeit wissen", "musik": "Musik hören"})})
        dauer = time.monotonic() - start
    except Exception as e:  # noqa: BLE001
        return FEHLER, f"Jev nicht erreichbar: {str(e)[:120]}"
    if antwort.answers["absicht"].choice != "uhrzeit":
        return HINWEIS, "Jev antwortet, aber merkwürdig"
    return OK, f"Jev antwortet ({dauer:.1f} s)"


def claude_anmeldung():
    import jev_assistent as j
    if not j.CONFIG.get("claude", {}).get("aktiv"):
        return OK, "Claude ist abgeschaltet (config.json)"
    import claude
    try:
        exe = claude._claude_exe()
        r = subprocess.run([exe, "auth", "status"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        daten = json.loads(r.stdout)
    except Exception as e:  # noqa: BLE001
        return HINWEIS, f"Claude nicht prüfbar ({str(e)[:80]}) - unklare Sätze versteht Jeff dann nicht"
    if not daten.get("loggedIn"):
        return HINWEIS, "Claude ist abgemeldet: im Terminal einmal \"claude\" starten und anmelden"
    return OK, "Claude angemeldet (Abo)"


def spotify():
    import jev_assistent as j
    if not j.CONFIG["spotify"]["client_id"]:
        return HINWEIS, ("Spotify-Zugang fehlt: \"spiel ...\" öffnet nur die Suche. Für echtes Abspielen "
                         "eine Client-ID in config.json eintragen, dann --spotify-login")
    if not j.SPOTIFY_TOKEN.exists():
        return HINWEIS, "Spotify-Client-ID da, aber nicht angemeldet: python jev_assistent.py --spotify-login"
    return OK, "Spotify eingerichtet"


def sprachausgabe():
    import pyttsx3
    try:
        stimmen = pyttsx3.init().getProperty("voices")
    except Exception as e:  # noqa: BLE001
        return HINWEIS, f"Sprachausgabe nicht nutzbar: {e}"
    if not any("German" in s.name or "Deutsch" in s.name for s in stimmen):
        return HINWEIS, "keine deutsche Windows-Stimme installiert - Jeff spricht mit englischem Akzent"
    return OK, "deutsche Stimme vorhanden"


def autostart():
    import autostart as a
    if not a.VERKNUEPFUNG.exists():
        return HINWEIS, "startet nicht mit Windows (python autostart.py ein)"
    if a.von_windows_gesperrt():
        return HINWEIS, ("in den Windows-Autostart-Apps ausgeschaltet - startet NICHT mit Windows "
                         "(python autostart.py ein)")
    return OK, "startet mit Windows"


PRUEFUNGEN = [("Pakete", pakete, False), ("Einstellungen", konfiguration, False), ("Modelle", modelle, False),
              ("Grafikkarte", gpu, False), ("Mikrofon", mikrofon, True), ("Jev", jev, True),
              ("Claude", claude_anmeldung, True), ("Spotify", spotify, False),
              ("Sprachausgabe", sprachausgabe, False), ("Autostart", autostart, False)]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    schnell = "--schnell" in sys.argv
    schlimmstes = OK
    print("Jeff-Selbsttest\n")
    for name, pruefung, langsam in PRUEFUNGEN:
        if schnell and langsam:
            continue
        try:
            stufe, text = pruefung()
        except Exception as e:  # noqa: BLE001 - eine kaputte Prüfung soll die anderen nicht aufhalten
            stufe, text = FEHLER, f"Prüfung abgestürzt: {e}"
        print(f"  {ZEICHEN[stufe]} {name:<14} {text}")
        if stufe == FEHLER or (stufe == HINWEIS and schlimmstes == OK):
            schlimmstes = stufe
    print()
    sys.exit({OK: 0, HINWEIS: 1, FEHLER: 2}[schlimmstes])


if __name__ == "__main__":
    main()
