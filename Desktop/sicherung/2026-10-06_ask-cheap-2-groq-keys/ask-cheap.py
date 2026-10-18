#!/usr/bin/env python3
"""ask-cheap – Routinearbeit an günstige/kostenlose LLM-APIs abgeben.

Beispiele:
  ask-cheap "Erkläre kurz, was ein Mutex ist"
  cat build.log | ask-cheap "Fasse die Fehler zusammen"
  ask-cheap --provider gemini --fast "Übersetze ins Englische: ..."
  ask-cheap --files a.log b.log --parallel 3 "Fasse zusammen"
  ask-cheap --test
  ask-cheap --set-key groq          (Key verdeckt eingeben, landet im Windows-Anmeldeinformations-Manager)

Keys werden gesucht in: Umgebungsvariable -> Windows-Anmeldeinformations-Manager
(Ziel "ask-cheap:<VARNAME>") -> ~/.config/ask-cheap/env. Keys werden nie ausgegeben.
"""
import argparse
import concurrent.futures
import json
import os
import re
import stat
import sys
import threading
import time
import urllib.error
import urllib.request

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "ask-cheap")
ENV_FILE = os.path.join(CONFIG_DIR, "env")
MODEL_CACHE = os.path.join(CONFIG_DIR, "models.json")
MODEL_CACHE_TTL = 24 * 3600

# Modellauswahl: Regex-Muster in Vorzugsreihenfolge, abgeglichen gegen GET /models.
# "fast" = kleine/schnelle Modelle für einfache Aufgaben.
PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1",
        "key": "GROQ_API_KEY",
        # Stand 06.10.2026 laut Groq-Konsole: gpt-oss-120b/20b, qwen3.8-27b (keine llama-Chatmodelle mehr)
        "prefer": [r"^openai/gpt-oss-120b$", r"^qwen/qwen3", r"^openai/gpt-oss-20b$"],
        "prefer_fast": [r"^openai/gpt-oss-20b$", r"^llama-3\.1-8b-instant$", r"^qwen/qwen3"],
        "rpm": 30, "tpm": 8000,
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key": "GEMINI_API_KEY",
        # 2.5 Flash-Lite wird am 16.10.2026 abgeschaltet -> bewusst nicht in der Liste.
        "prefer": [r"^gemini-3\.1-flash-lite$", r"^gemini-3\.1-flash-lite-\d", r"^gemini-3\.1-flash-lite",
                   r"^gemini-3(\.\d)?-flash$", r"^gemini-3(\.\d)?-flash"],
        "prefer_fast": [r"^gemini-3\.1-flash-lite$", r"^gemini-3\.1-flash-lite"],
        "rpm": 15, "tpm": 250000,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1",
        "key": "OPENROUTER_API_KEY",
        # Stand 06.10.2026 (kein gpt-oss mehr gratis); Liste prüfen mit: ask-cheap --list-models openrouter
        "prefer": [r"^openai/gpt-oss-120b:free$", r"^nvidia/nemotron-3-super-.*:free$", r"^google/gemma-4-31b-it:free$",
                   r"^deepseek/.*:free$", r"^qwen/.*:free$", r":free$"],
        "prefer_fast": [r"^google/gemma-4-26b-a4b-it:free$", r"^nvidia/nemotron-3\.5-lightning:free$", r":free$"],
        "rpm": 20, "tpm": 10**9,
    },
    "deepseek": {  # kostet Geld, Server in China -> nicht in der Standard-Kette
        "url": "https://api.deepseek.com",
        "key": "DEEPSEEK_API_KEY",
        "prefer": [r"flash", r"^deepseek-chat$", r"^deepseek-v"],
        "prefer_fast": [r"flash", r"^deepseek-chat$"],
        "rpm": 60, "tpm": 10**9,
    },
}
DEFAULT_CHAIN = ["groq", "gemini", "openrouter"]
MAX_RETRY_AFTER = 20  # Sekunden: länger warten wir nicht, dann lieber nächster Anbieter


def log(msg):
    print(f"[ask-cheap] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- Keys

def _cred_structs():
    import ctypes
    from ctypes import wintypes

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                    ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                    ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
                    ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                    ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]
    return ctypes, wintypes, CREDENTIAL, ctypes.WinDLL("advapi32", use_last_error=True)


def wincred_read(name):
    if os.name != "nt":
        return None
    try:
        ctypes, wintypes, CREDENTIAL, adv = _cred_structs()
        p = ctypes.POINTER(CREDENTIAL)()
        if not adv.CredReadW(f"ask-cheap:{name}", 1, 0, ctypes.byref(p)):
            return None
        try:
            c = p.contents
            raw = bytes(ctypes.cast(c.CredentialBlob, ctypes.POINTER(ctypes.c_ubyte * c.CredentialBlobSize)).contents) \
                if c.CredentialBlobSize else b""
        finally:
            adv.CredFree(p)
        # cmdkey und --set-key speichern UTF-16LE
        if len(raw) % 2 == 0 and raw[1::2] == b"\0" * (len(raw) // 2):
            return raw.decode("utf-16-le").strip() or None
        return raw.decode("utf-8", "replace").strip() or None
    except Exception:
        return None


def wincred_write(name, secret):
    ctypes, wintypes, CREDENTIAL, adv = _cred_structs()
    blob = secret.encode("utf-16-le")
    buf = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    c = CREDENTIAL()
    c.Type = 1  # CRED_TYPE_GENERIC
    c.TargetName = f"ask-cheap:{name}"
    c.UserName = "ask-cheap"
    c.CredentialBlobSize = len(blob)
    c.CredentialBlob = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))
    c.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
    if not adv.CredWriteW(ctypes.byref(c), 0):
        raise OSError(f"CredWriteW fehlgeschlagen (Fehler {ctypes.get_last_error()})")


def envfile_values():
    vals = {}
    try:
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip().removeprefix("export ").strip()
                v = v.strip().strip('"').strip("'")
                if v:
                    vals[k] = v
    except FileNotFoundError:
        pass
    return vals


_ENV_CACHE = None


def get_key(var):
    global _ENV_CACHE
    if os.environ.get(var):
        return os.environ[var]
    v = wincred_read(var)
    if v:
        return v
    if _ENV_CACHE is None:
        _ENV_CACHE = envfile_values()
    return _ENV_CACHE.get(var)


def redact(text, *secrets):
    for s in secrets:
        if s:
            text = text.replace(s, "***")
    return re.sub(r"(sk-|gsk_|AIza)[A-Za-z0-9_\-]{8,}", r"\1***", text)


# ---------------------------------------------------------------- HTTP

class ApiError(Exception):
    def __init__(self, status, msg, headers=None):
        super().__init__(msg)
        self.status = status
        self.headers = headers or {}


def http(method, url, key, body=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "ask-cheap/1.0")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    if "openrouter.ai" in url:
        req.add_header("X-Title", "ask-cheap")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            j = json.loads(raw)
            err = j[0] if isinstance(j, list) and j else j
            msg = (err.get("error") or {}).get("message") if isinstance(err.get("error"), dict) else err.get("error")
            msg = msg or raw
        except Exception:
            msg = raw
        msg = str(msg).strip() or "(leere Fehlerantwort – Key oder Anfrage ungültig?)"
        raise ApiError(e.code, redact(msg[:400], key), dict(e.headers)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ApiError(0, f"Netzwerkfehler: {e}") from None


# ---------------------------------------------------------------- Modelle

def _load_cache():
    try:
        with open(MODEL_CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def list_models(provider, key, refresh=False):
    cache = _load_cache()
    ent = cache.get(provider)
    if ent and not refresh and time.time() - ent.get("t", 0) < MODEL_CACHE_TTL:
        return ent["ids"]
    j, _ = http("GET", PROVIDERS[provider]["url"] + "/models", key, timeout=30)
    ids = sorted({m["id"].removeprefix("models/") for m in j.get("data", []) if m.get("id")})
    cache[provider] = {"t": time.time(), "ids": ids}
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(MODEL_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1)
    except OSError:
        pass
    return ids


def blocked_models(provider):
    ent = _load_cache().get("_blocked", {}).get(provider, {})
    return {m for m, t in ent.items() if time.time() - t < MODEL_CACHE_TTL}


def mark_blocked(provider, model):
    """Modell steht in /models, ist aber für diesen Key gesperrt (z. B. Groq-Projektlimits) -> 24 h überspringen."""
    cache = _load_cache()
    cache.setdefault("_blocked", {}).setdefault(provider, {})[model] = time.time()
    try:
        with open(MODEL_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1)
    except OSError:
        pass


def unmark_blocked(provider, model):
    cache = _load_cache()
    if cache.get("_blocked", {}).get(provider, {}).pop(model, None) is not None:
        try:
            with open(MODEL_CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=1)
        except OSError:
            pass


def pick_models(provider, key, fast=False, refresh=False):
    """Kandidaten in Vorzugsreihenfolge (ohne gesperrte). Erst die bevorzugte Liste, dann die andere als Reserve."""
    cfg = PROVIDERS[provider]
    patterns = cfg["prefer_fast"] + cfg["prefer"] if fast else cfg["prefer"] + cfg["prefer_fast"]
    try:
        ids = list_models(provider, key, refresh)
    except ApiError:
        ids = []
    if not ids:  # /models nicht erreichbar: Muster ohne Regex-Zeichen als Vermutung
        return [re.sub(r"[\^\$\\]", "", patterns[0])]
    blocked = set() if refresh else blocked_models(provider)
    out = []
    for pat in patterns:
        hits = [i for i in ids if re.search(pat, i) and i not in blocked
                and not re.search(r"2\.5-flash-lite|safety|guard|embed|tts|image|audio|whisper|orpheus", i)]
        hits.sort(key=lambda h: "preview" in h or "exp" in h)  # stabile zuerst
        out += [h for h in hits if h not in out]
    if not out:
        raise ApiError(0, f"kein passendes/freigegebenes Modell gefunden (nutze --model, --list-models {provider})")
    return out


def chat_any(provider, key, messages, args, limit=True):
    """Probiert die Modell-Kandidaten eines Anbieters durch; 403/404 aufs Modell -> nächstes Modell."""
    candidates = [args.model] if args.model else pick_models(provider, key, args.fast, refresh=getattr(args, "test", False))
    last = None
    for i, model in enumerate(candidates):
        can_switch = i < len(candidates) - 1  # Limits gelten pro Modell -> erst wechseln, beim letzten warten
        try:
            content, headers = chat(provider, model, key, messages, args, limit, can_switch)
            return model, content, headers
        except ApiError as e:
            if e.status in (429, 413) and can_switch:
                if args.verbose:
                    log(f"{provider}: {model} am Limit (HTTP {e.status}), wechsle zu {candidates[i + 1]}")
                last = e
                continue
            if e.status in (403, 404) and not args.model:
                mark_blocked(provider, model)
                if args.verbose:
                    log(f"{provider}: {model} gesperrt/unbekannt (HTTP {e.status}), nächstes Modell")
                last = e
                continue
            raise
    raise last


# ---------------------------------------------------------------- Rate-Limit

class Limiter:
    """Gleitendes 60-s-Fenster für Anfragen (RPM) und geschätzte Tokens (TPM) je Anbieter."""

    def __init__(self, rpm, tpm):
        self.rpm, self.tpm = rpm, tpm
        self.events = []  # (zeit, tokens)
        self.lock = threading.Lock()

    def acquire(self, tokens, block=True):
        tokens = min(tokens, self.tpm)
        while True:
            with self.lock:
                now = time.time()
                self.events = [e for e in self.events if now - e[0] < 60]
                used = sum(t for _, t in self.events)
                if len(self.events) < self.rpm and used + tokens <= self.tpm:
                    self.events.append((now, tokens))
                    return True
                if not block:
                    return False
                wait = 60 - (now - self.events[0][0]) + 0.05 if self.events else 1
            time.sleep(max(0.2, wait))


_LIMITERS, _LIMITERS_LOCK = {}, threading.Lock()


def limiter(provider, model):
    """Groq & Co. zählen die Limits pro Modell -> eigener Zähler je (Anbieter, Modell)."""
    with _LIMITERS_LOCK:
        if (provider, model) not in _LIMITERS:
            c = PROVIDERS[provider]
            _LIMITERS[(provider, model)] = Limiter(c["rpm"], c["tpm"])
        return _LIMITERS[(provider, model)]


def est_tokens(messages, max_tokens):
    # Groq zählt bei Logs/Zahlen deutlich mehr als Zeichen/4 (gemessen: ~Zeichen/2.3) -> vorsichtig schätzen
    return int(sum(len(m["content"]) for m in messages) / 2.3) + (max_tokens or 1024)


# ---------------------------------------------------------------- Anfrage

def chat(provider, model, key, messages, args, limit=True, can_switch=False):
    body = {"model": model, "messages": messages}
    if args.max_tokens:
        body["max_tokens"] = args.max_tokens
    if args.temperature is not None:
        body["temperature"] = args.temperature
    if provider == "groq" and "gpt-oss" in model:
        body["reasoning_effort"] = args.reasoning or "low"
        if getattr(args, "web", False):  # Groq-eigene Websuche (nur gpt-oss), kostet ~7-10k Tokens
            body["tools"] = [{"type": "browser_search"}]
            body["tool_choice"] = "auto"
    if limit:
        if not limiter(provider, model).acquire(est_tokens(messages, args.max_tokens), block=not can_switch):
            raise ApiError(429, "lokales Minutenlimit erreicht")
    waited = 0.0
    for attempt in range(5):
        try:
            j, headers = http("POST", PROVIDERS[provider]["url"] + "/chat/completions", key, body, timeout=args.timeout)
            msg = (j.get("choices") or [{}])[0].get("message") or {}
            content = msg.get("content")
            if not content:
                raise ApiError(0, "leere Antwort")
            if msg.get("executed_tools"):
                urls = list(dict.fromkeys(re.findall(r"https?://[^\s\"'\\)\]>]+", json.dumps(msg["executed_tools"]))))
                content = re.sub(r"【[^】]*】", "", content)
                if urls:
                    content += "\n\nQuellen (Websuche, bitte prüfen):\n" + "\n".join(f"- {u}" for u in urls[:6])
            return content, headers
        except ApiError as e:
            if e.status not in (429, 500, 502, 503, 504) or attempt == 4 or (e.status == 429 and can_switch):
                raise
            ra = e.headers.get("retry-after") or e.headers.get("Retry-After")
            m = re.search(r"try again in (?:(\d+)m)?([\d.]+)(ms|s)", str(e))
            try:
                wait = float(ra) if ra else 2.0 * (attempt + 1)
            except ValueError:
                wait = 2.0
            if m:  # Groq nennt die genaue Wartezeit im Text
                wait = max(wait, int(m.group(1) or 0) * 60 + float(m.group(2)) / (1000 if m.group(3) == "ms" else 1))
            wait += 0.5
            # Gibt es noch einen anderen Anbieter, lieber wechseln statt lange warten; sonst bis ~70 s warten
            limit_wait = 70 if getattr(args, "_last_provider", True) else MAX_RETRY_AFTER
            if wait > limit_wait or waited + wait > limit_wait:
                raise
            if args.verbose:
                log(f"{provider}: HTTP {e.status}, warte {wait:.1f}s (Versuch {attempt + 2}/5)")
            time.sleep(wait)
            waited += wait


def run(messages, args):
    chain = [args.provider] if args.provider else (os.environ.get("ASK_CHEAP_CHAIN", "").split(",") if os.environ.get("ASK_CHEAP_CHAIN") else DEFAULT_CHAIN)
    errors = []
    chain = [p.strip() for p in chain if p.strip()]
    if getattr(args, "web", False):
        chain = [p for p in chain if p == "groq"] or ["groq"]  # Websuche gibt es nur bei Groq
    usable = [p for p in chain if p in PROVIDERS and get_key(PROVIDERS[p]["key"]) and not key_problem(get_key(PROVIDERS[p]["key"]))]
    for provider in chain:
        args._last_provider = bool(usable) and provider == usable[-1]
        if provider not in PROVIDERS:
            errors.append(f"{provider}: unbekannter Anbieter")
            continue
        key = get_key(PROVIDERS[provider]["key"])
        if not key:
            errors.append(f"{provider}: kein Key ({PROVIDERS[provider]['key']})")
            continue
        if key_problem(key):
            errors.append(f"{provider}: Key {key_problem(key)}".replace("<anbieter>", provider))
            continue
        try:
            model, content, _ = chat_any(provider, key, messages, args)
            if args.verbose:
                log(f"Antwort von {provider} / {model}")
            return content
        except ApiError as e:
            msg = f"{provider}: HTTP {e.status} {e}" if e.status else f"{provider}: {e}"
            if e.status == 413:
                msg = f"{provider}: Eingabe zu groß für das Gratis-Limit (HTTP 413) – Eingabe kürzen/aufteilen oder Gemini-Key hinterlegen"
            errors.append(msg)
            if args.verbose:
                log(errors[-1])
    raise SystemExit("[ask-cheap] Kein Anbieter hat geantwortet:\n  " + "\n  ".join(errors))


# ---------------------------------------------------------------- Test

def cmd_test(args):
    print(f"{'Anbieter':<11} {'Status':<8} Modell / Details")
    for provider, cfg in PROVIDERS.items():
        key = get_key(cfg["key"])
        if not key:
            print(f"{provider:<11} {'—':<8} kein Key hinterlegt ({cfg['key']})")
            continue
        if key_problem(key):
            print(f"{provider:<11} {'FEHLER':<8} Key {key_problem(key)}".replace("<anbieter>", provider))
            continue
        try:
            t0 = time.time()
            model, content, headers = chat_any(provider, key,
                                               [{"role": "user", "content": "Antworte nur mit dem Wort: ok"}],
                                               argparse.Namespace(**{**vars(args), "max_tokens": args.max_tokens or 300}),
                                               limit=False)
            dt = time.time() - t0
            unmark_blocked(provider, model)
            print(f"{provider:<11} {'ok':<8} {model}  ({dt:.1f}s, Antwort: {content.strip()[:20]!r})")
            rl = {k.lower(): v for k, v in headers.items()
                  if k.lower().startswith(("x-ratelimit", "ratelimit", "retry-after"))}
            for k in sorted(rl):
                print(f"{'':<20}{k}: {rl[k]}")
            if not rl:
                print(f"{'':<20}(keine Rate-Limit-Header geliefert)")
            if not args.model:
                others = [m for m in pick_models(provider, key, refresh=True) if m != model][:4]
                status = []
                for m in others:
                    try:
                        chat(provider, m, key, [{"role": "user", "content": "ok"}],
                             argparse.Namespace(**{**vars(args), "max_tokens": 300}), limit=False)
                        unmark_blocked(provider, m)
                        status.append(f"{m} ok")
                    except ApiError as e:
                        if e.status in (403, 404):
                            mark_blocked(provider, m)
                        status.append(f"{m} " + ("GESPERRT" if e.status in (403, 404) else f"HTTP {e.status}"))
                if status:
                    print(f"{'':<20}weitere Modelle: " + ", ".join(status))
        except ApiError as e:
            print(f"{provider:<11} {'FEHLER':<8} HTTP {e.status}: {e}" if e.status else f"{provider:<11} {'FEHLER':<8} {e}")


def key_problem(key):
    """Grobe Plausibilitätsprüfung, ohne den Key preiszugeben."""
    if any(ord(c) < 32 for c in key):
        return "enthält Steuerzeichen (vermutlich Strg+V statt Key gespeichert) – neu setzen mit: ask-cheap --set-key <anbieter> --clipboard"
    if len(key) < 20:
        return f"zu kurz ({len(key)} Zeichen) – neu setzen mit: ask-cheap --set-key <anbieter> --clipboard"
    return None


def read_clipboard():
    import subprocess
    out = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                         capture_output=True, text=True, encoding="utf-8")
    return out.stdout.strip()


def clear_clipboard():
    import subprocess
    subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ' '"], capture_output=True)


def cmd_set_key(provider, from_clipboard=False):
    import getpass
    var = PROVIDERS[provider]["key"]
    if from_clipboard:
        secret = read_clipboard()
    else:
        secret = getpass.getpass(f"{var} eingeben (unsichtbar; Einfügen per Rechtsklick, NICHT Strg+V): ").strip()
    if not secret:
        raise SystemExit("Abgebrochen, nichts gespeichert.")
    problem = key_problem(secret)
    if problem:
        raise SystemExit(f"Nicht gespeichert: Eingabe {problem}")
    if os.name == "nt":
        wincred_write(var, secret)
        print(f"Gespeichert im Windows-Anmeldeinformations-Manager als 'ask-cheap:{var}'.")
    else:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        lines = [l for l in (open(ENV_FILE).read().splitlines() if os.path.exists(ENV_FILE) else [])
                 if not l.strip().startswith(var + "=")]
        lines.append(f"{var}={secret}")
        fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(lines) + "\n")
        os.chmod(ENV_FILE, stat.S_IRUSR | stat.S_IWUSR)
        print(f"Gespeichert in {ENV_FILE} (chmod 600).")
    if from_clipboard:
        clear_clipboard()
        print("Zwischenablage geleert.")
    print(f"Prüfen mit: ask-cheap --test")


# ---------------------------------------------------------------- Main

STDIN_GRACE = 3.0  # Sekunden: so lange warten wir auf erste Daten aus einer offenen, stummen Pipe


def read_stdin(args, have_prompt):
    """Liest gepipte Eingabe. Manche Umgebungen (z. B. Claude Code) geben eine offene Pipe als stdin,
    in die nie etwas geschrieben wird – dann nach STDIN_GRACE Sekunden ohne Daten ignorieren,
    statt ewig zu hängen. --stdin erzwingt unbegrenztes Warten (für langsame Erzeuger)."""
    if args.no_stdin:
        return ""
    try:
        mode = os.fstat(0).st_mode
    except OSError:
        return ""
    if stat.S_ISREG(mode):
        return sys.stdin.buffer.read().decode("utf-8", "replace")
    if not stat.S_ISFIFO(mode):
        return ""
    if args.stdin or not have_prompt:
        return sys.stdin.buffer.read().decode("utf-8", "replace")
    chunks, first = [], threading.Event()

    def reader():
        while True:
            b = sys.stdin.buffer.read1(65536)
            chunks.append(b)
            first.set()
            if not b:
                return

    threading.Thread(target=reader, daemon=True).start()
    if not first.wait(STDIN_GRACE):
        if args.verbose:
            log(f"stdin ignoriert (keine Daten in {STDIN_GRACE:.0f}s; --stdin erzwingt Warten)")
        return None  # Signal: Reader-Thread hängt noch -> am Ende hart beenden
    while chunks[-1] != b"":
        time.sleep(0.01)
    return b"".join(chunks).decode("utf-8", "replace")


DEFAULT_SYSTEM = ("Antworte knapp und präzise in der Sprache der Anfrage. Keine Einleitung, keine Wiederholung der "
                  "Aufgabe, keine Tabellen oder Überschriften außer wenn verlangt, keine Ratschläge oder Angebote, "
                  "die nicht erfragt wurden. Wenn etwas nicht in den gegebenen Daten steht, sag das statt zu raten.")


def build_messages(prompt, extra, args):
    msgs = []
    system = DEFAULT_SYSTEM if args.system is None else args.system
    if system:
        msgs.append({"role": "system", "content": system})
    content = prompt
    if extra:
        content = f"{prompt}\n\n---\n{extra}" if prompt else extra
    msgs.append({"role": "user", "content": content})
    return msgs


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="ask-cheap", description="Günstige LLM-APIs für Routinearbeit (Groq -> Gemini -> OpenRouter).")
    ap.add_argument("prompt", nargs="*", help="Prompt (stdin wird angehängt, falls etwas hereingepiped wird)")
    ap.add_argument("--provider", "-p", choices=list(PROVIDERS), help="nur diesen Anbieter nutzen (kein Wechsel)")
    ap.add_argument("--model", "-m", help="Modell-ID erzwingen")
    ap.add_argument("--fast", action="store_true", help="kleines/schnelles Modell (z. B. gpt-oss-20b)")
    ap.add_argument("--web", action="store_true", help="Websuche erlauben (nur Groq/gpt-oss, ~8k Tokens pro Anfrage, Ergebnisse prüfen!)")
    ap.add_argument("--system", "-s", help='System-Prompt (Standard: "knapp antworten"; --system "" schaltet ihn ab)')
    ap.add_argument("--max-tokens", type=int)
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--reasoning", choices=["low", "medium", "high"], help="reasoning_effort für gpt-oss (Standard: low)")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--files", nargs="+", metavar="DATEI", help="jede Datei einzeln mit dem Prompt senden")
    ap.add_argument("--parallel", type=int, default=1, metavar="N", help="bis zu N Anfragen gleichzeitig (mit RPM/TPM-Bremse)")
    ap.add_argument("--test", action="store_true", help="alle hinterlegten Keys mit Mini-Anfrage prüfen")
    ap.add_argument("--list-models", metavar="ANBIETER", choices=list(PROVIDERS))
    ap.add_argument("--set-key", metavar="ANBIETER", choices=list(PROVIDERS), help="Key verdeckt eingeben und sicher speichern")
    ap.add_argument("--clipboard", action="store_true", help="mit --set-key: Key aus der Zwischenablage lesen (und sie danach leeren)")
    ap.add_argument("--stdin", action="store_true", help="unbegrenzt auf gepipte Eingabe warten (für langsame Befehle davor)")
    ap.add_argument("--no-stdin", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("-v", "--verbose", action="store_true", help="Anbieter/Modell und Fehler auf stderr ausgeben")
    args = ap.parse_args()

    if args.set_key:
        return cmd_set_key(args.set_key, args.clipboard)
    if args.test:
        return cmd_test(args)
    if args.list_models:
        key = get_key(PROVIDERS[args.list_models]["key"])
        for m in list_models(args.list_models, key, refresh=True):
            print(m)
        return

    prompt = " ".join(args.prompt).strip()

    if args.files:
        # Prompt hinter --files wird von argparse als Datei geschluckt -> zurückholen
        if not prompt and args.files and not os.path.exists(args.files[-1]):
            prompt = args.files.pop()
        missing = [p for p in args.files if not os.path.exists(p)]
        if missing:
            ap.error(f"Datei(en) nicht gefunden: {', '.join(missing)}")
        if not prompt:
            ap.error("mit --files bitte auch einen Prompt angeben (z. B. ask-cheap \"Fasse zusammen\" --files a.log)")

        def one(path):
            with open(path, encoding="utf-8", errors="replace") as f:
                return run(build_messages(prompt, f.read(), args), args)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
            futs = {p: ex.submit(one, p) for p in args.files}
            for path, fut in futs.items():
                print(f"=== {path} ===")
                try:
                    print(fut.result().strip())
                except BaseException as e:  # SystemExit aus run() abfangen, andere Dateien weiterlaufen lassen
                    print(f"[Fehler] {e}")
                print()
        return

    extra = read_stdin(args, bool(prompt))
    if not prompt and not extra:
        ap.error("kein Prompt angegeben")
    try:
        print(run(build_messages(prompt, extra or "", args), args).strip(), flush=True)
        code = 0
    except SystemExit as e:
        if extra is not None:
            raise
        print(e, file=sys.stderr)
        code = 1
    if extra is None:  # blockierter stdin-Reader würde das Beenden verzögern -> hart beenden
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)


if __name__ == "__main__":
    main()
