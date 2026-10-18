"""Claude als Sprachverständnis für Jeff.

Jev entscheidet schnell zwischen festen Absichten. Versteht er einen Satz nicht,
deutet Claude ihn: entweder als klaren Befehl, den Jeff dann ausführt, oder als
Frage, die Claude direkt beantwortet. Läuft über die Claude-CLI (Abo, kein API-Key),
ohne Werkzeuge, Hooks, Plugins und ohne gespeicherte Sitzung.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

BASIS = Path(__file__).resolve().parent
ARBEITSORDNER = BASIS / "claude-leer"   # leerer Ordner: keine CLAUDE.md, kein Projekt


class ClaudeFehler(Exception):
    pass


def _config():
    return json.loads((BASIS / "config.json").read_text(encoding="utf-8"))


def _faehigkeiten(absichten):
    """Was Jeff kann, als Liste für Claude - direkt aus den Absichten erzeugt."""
    zeilen = []
    for name, a in absichten.items():
        if name in ("sonstiges", "claude_fragen"):
            continue
        beispiele = "; ".join(a.get("examples", [])[:3])
        zeilen.append(f"- {a['what']} (z. B.: {beispiele})")
    return "\n".join(zeilen)


def systemprompt(absichten):
    cfg = _config()
    apps = ", ".join(a["beschreibung"].split(",")[0] for a in cfg["apps"].values())
    seiten = ", ".join(s["beschreibung"].split(",")[0] for s in cfg["webseiten"].values())
    return f"""Du bist das Sprachverständnis von Jeff, einem deutschen Sprachassistenten auf einem Windows-PC.
Du bekommst einen gesprochenen Satz aus einer Spracherkennung (Whisper). Er kann falsch erkannte Wörter,
Umgangssprache und Füllwörter enthalten. `alternativ` ist eine zweite, ungenauere Erkennung desselben Satzes.

Das kann Jeff am PC ausführen:
{_faehigkeiten(absichten)}
Bekannte Programme: {apps}. Bekannte Webseiten: {seiten}.

Entscheide, was die Person meint, und antworte mit GENAU EINER JSON-Zeile, ohne Codeblock:
{{"art": "befehl" | "antwort" | "unklar", "befehl": "...", "antwort": "..."}}

- "befehl": Die Person will etwas am PC, das Jeff kann. Schreib in "befehl" einen kurzen, klaren deutschen
  Befehl im Stil der Beispiele, mit korrigierten Erkennungsfehlern und richtigen Namen
  (z. B. "mach mal die mucke von dem apache typ an" -> "spiel was von apache 207").
- "antwort": Eine Frage, Bitte um Erklärung, Übersetzung, Rat oder Plauderei. Schreib in "antwort" eine kurze
  Antwort zum Vorlesen: höchstens drei Sätze, keine Aufzählungen, kein Markdown, Zahlen als Wörter wo sinnvoll.
- "unklar": Nur Bruchstücke, Hintergrundgerede oder etwas, das Jeff nicht kann. Schreib in "antwort" eine
  sehr kurze Rückfrage oder Erklärung, was nicht geht.
Du kannst selbst nichts ausführen und nichts nachschlagen; erfinde keine aktuellen Fakten (Nachrichten, Kurse)."""


def _claude_exe():
    exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    if not Path(exe).exists():
        raise ClaudeFehler("claude.exe nicht gefunden")
    return exe


def _json_aus(text):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ClaudeFehler(f"keine JSON-Antwort: {text[:200]}")
    return json.loads(m.group(0))


def frage(text, absichten, alternativ=None, kontext=None):
    """Satz von Claude deuten lassen. -> {"art", "befehl", "antwort"}"""
    cfg = _config().get("claude", {})
    ARBEITSORDNER.mkdir(exist_ok=True)
    eingabe = {"gesprochen": text}
    if alternativ and alternativ.lower() != text.lower():
        eingabe["alternativ"] = alternativ
    if kontext:
        eingabe["kontext"] = kontext
    befehl = [_claude_exe(), "-p", "--model", cfg.get("modell", "sonnet"),
              "--tools", "", "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence",
              "--output-format", "json", "--system-prompt", systemprompt(absichten)]
    umgebung = {**os.environ, "MAX_THINKING_TOKENS": "0"}
    try:
        lauf = subprocess.run(befehl, input=json.dumps(eingabe, ensure_ascii=False), cwd=ARBEITSORDNER, env=umgebung,
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=cfg.get("zeitlimit_sekunden", 25),
                              creationflags=subprocess.CREATE_NO_WINDOW)  # kein Konsolenfenster, das den Fokus klaut
    except subprocess.TimeoutExpired as e:
        raise ClaudeFehler("Zeitlimit") from e
    except OSError as e:
        raise ClaudeFehler(str(e)) from e
    try:
        antwort = json.loads(lauf.stdout)
    except json.JSONDecodeError as e:
        raise ClaudeFehler(f"CLI-Ausgabe unlesbar: {(lauf.stdout or lauf.stderr)[:200]}") from e
    if antwort.get("is_error"):
        raise ClaudeFehler(str(antwort.get("result"))[:200])
    try:
        return _json_aus(antwort.get("result", ""))
    except json.JSONDecodeError as e:
        raise ClaudeFehler(f"JSON kaputt: {antwort.get('result', '')[:200]}") from e


if __name__ == "__main__":
    import sys
    from jev_assistent import ABSICHTEN
    print(frage(" ".join(sys.argv[1:]) or "mach mal die mucke von dem apache typ an", ABSICHTEN))
