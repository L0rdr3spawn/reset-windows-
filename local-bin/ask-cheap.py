#!/usr/bin/env python3
"""ask-cheap – Routinearbeit an günstige/kostenlose LLM-APIs abgeben.

Beispiele:
  ask-cheap "Erkläre kurz, was ein Mutex ist"
  cat build.log | ask-cheap "Fasse die Fehler zusammen"
  ask-cheap --provider gemini --fast "Übersetze ins Englische: ..."
  ask-cheap --files a.log b.log --parallel 3 "Fasse zusammen"
  ask-cheap --test
  ask-cheap --set-key groq          (Key verdeckt eingeben, landet im Windows-Anmeldeinformations-Manager)
  ask-cheap --set-key groq2         (zweiter Account: GROQ_API_KEY_2)

Keys werden gesucht in: Umgebungsvariable -> Windows-Anmeldeinformations-Manager
(Ziel "ask-cheap:<VARNAME>") -> ~/.config/ask-cheap/env. Keys werden nie ausgegeben.

Mehrere Accounts je Anbieter (z. B. groq + groq2): Anfragen gehen an den Account mit dem meisten
Restbudget (laut Rate-Limit-Headern, gemerkt in ~/.config/ask-cheap/limits.json). Ist einer am Limit,
geht dieselbe Anfrage sofort an den nächsten – gewartet wird erst, wenn alle Accounts/Modelle voll sind.
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
STATE_FILE = os.path.join(CONFIG_DIR, "limits.json")  # Restbudget/Sperrzeiten je Account+Modell, prozessübergreifend
MAX_ACCOUNTS = 5  # GROQ_API_KEY, GROQ_API_KEY_2 … GROQ_API_KEY_5

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


def key_var(provider, n=1):
    base = PROVIDERS[provider]["key"]
    return base if n == 1 else f"{base}_{n}"


def acct_name(provider, n=1):
    return provider if n == 1 else f"{provider}{n}"


def parse_acct(name):
    """'groq' -> ('groq', 1), 'groq2' -> ('groq', 2)."""
    m = re.fullmatch(r"([a-z]+?)(\d*)", name or "")
    if not m or m.group(1) not in PROVIDERS or not 1 <= int(m.group(2) or 1) <= MAX_ACCOUNTS:
        raise ValueError(f"unbekannter Anbieter/Account: {name} (z. B. groq, groq2, gemini)")
    return m.group(1), int(m.group(2) or 1)


_ACCOUNTS = {}


def get_accounts(provider, problems=None):
    """Alle hinterlegten Keys eines Anbieters als [(accountname, key)], z. B. [('groq', …), ('groq2', …)].
    Kaputte Keys landen in `problems`, doppelt gespeicherte Keys zählen nur einmal."""
    if provider not in _ACCOUNTS:
        good, bad, seen = [], [], set()
        for n in range(1, MAX_ACCOUNTS + 1):
            k = get_key(key_var(provider, n))
            if not k or k in seen:
                continue
            seen.add(k)
            p = key_problem(k)
            if p:
                bad.append(f"{acct_name(provider, n)}: Key {p}".replace("<anbieter>", acct_name(provider, n)))
            else:
                good.append((acct_name(provider, n), k))
        _ACCOUNTS[provider] = (good, bad)
    good, bad = _ACCOUNTS[provider]
    if problems is not None:
        problems += bad
    return good


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


def blocked_models(acct):
    ent = _load_cache().get("_blocked", {}).get(acct, {})
    return {m for m, t in ent.items() if time.time() - t < MODEL_CACHE_TTL}


def mark_blocked(acct, model):
    """Modell steht in /models, ist aber für diesen Key gesperrt (z. B. Groq-Projektlimits) -> 24 h überspringen."""
    cache = _load_cache()
    cache.setdefault("_blocked", {}).setdefault(acct, {})[model] = time.time()
    try:
        with open(MODEL_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1)
    except OSError:
        pass


def unmark_blocked(acct, model):
    cache = _load_cache()
    if cache.get("_blocked", {}).get(acct, {}).pop(model, None) is not None:
        try:
            with open(MODEL_CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=1)
        except OSError:
            pass


def pick_models(provider, key, fast=False, refresh=False, acct=None):
    """Kandidaten in Vorzugsreihenfolge (ohne die für `acct` gesperrten; acct="" = nichts ausfiltern).
    Erst die bevorzugte Liste, dann die andere als Reserve."""
    cfg = PROVIDERS[provider]
    patterns = cfg["prefer_fast"] + cfg["prefer"] if fast else cfg["prefer"] + cfg["prefer_fast"]
    try:
        ids = list_models(provider, key, refresh)
    except ApiError:
        ids = []
    if not ids:  # /models nicht erreichbar: Muster ohne Regex-Zeichen als Vermutung
        return [re.sub(r"[\^\$\\]", "", patterns[0])]
    blocked = set() if refresh or acct == "" else blocked_models(acct or provider)
    out = []
    for pat in patterns:
        hits = [i for i in ids if re.search(pat, i) and i not in blocked
                and not re.search(r"2\.5-flash-lite|safety|guard|embed|tts|image|audio|whisper|orpheus", i)]
        hits.sort(key=lambda h: "preview" in h or "exp" in h)  # stabile zuerst
        out += [h for h in hits if h not in out]
    if not out:
        raise ApiError(0, f"kein passendes/freigegebenes Modell gefunden (nutze --model, --list-models {provider})")
    return out


# Fehler, die den ganzen Account betreffen (nicht nur ein Modell) -> Account für diese Anfrage überspringen
ACCOUNT_ERR = re.compile(r"invalid api key|organi[sz]ation.*(restrict|disabl|suspend|block)|account.*(suspend|disabl|block)", re.I)


def chat_any(provider, accounts, messages, args, limit=True):
    """Schickt die Anfrage an die beste (Account, Modell)-Kombination. Limit (429/413) -> sofort, ohne Warten,
    die nächste Kombination (anderer Account bzw. anderes Modell); 403/404 aufs Modell -> für diesen Account 24 h
    überspringen; Key ungültig -> Account überspringen. Erst wenn alles voll ist, wird gewartet – und zwar auf die
    Kombination, die als erste wieder frei ist. Rückgabe: (account, modell, antwort, header)."""
    test = getattr(args, "test", False)
    models = [args.model] if args.model else pick_models(provider, accounts[0][1], args.fast, refresh=test, acct="")
    skip = {} if args.model or test else {a: blocked_models(a) for a, _ in accounts}
    planned = [c for c in plan(accounts, models, est_tokens(messages, args.max_tokens)) if c[2] not in skip.get(c[0], ())]
    if not planned:
        raise ApiError(0, f"kein passendes/freigegebenes Modell gefunden (nutze --model, --list-models {provider})")
    # Gemerkte Sperren (429 mit Wartezeit) gar nicht erst anfragen; knappes Budget ist nur geschätzt -> trotzdem probieren
    cands = [c[:3] for c in planned if not c[3]]
    limited = [c[:3] for c in planned if c[3]]
    last = last_limit = ApiError(429, "alle Accounts/Modelle gerade am Limit")
    dead = set()
    for i, (acct, key, model) in enumerate(cands):
        if acct in dead:
            continue
        try:
            content, headers = chat(provider, model, key, messages, args, limit, can_switch=True)
            remember_headers(acct, model, headers)
            return acct, model, content, headers
        except ApiError as e:
            last = e
            nxt = next((c for c in cands[i + 1:] if c[0] not in dead), None)
            if e.status in (429, 413):
                if e.status == 429:
                    last_limit = e
                    limited.append((acct, key, model))
                    if not str(e).startswith("lokales"):
                        save_slot(acct, model, until=time.time() + wait_hint(e, 5.0))
                if args.verbose and nxt:
                    why = "am Limit" if e.status == 429 else "Eingabe zu groß"
                    log(f"{acct}: {model} {why} (HTTP {e.status}) -> sofort weiter mit {nxt[0]} / {nxt[2]}")
                continue
            if e.status == 401 or ACCOUNT_ERR.search(str(e)):
                dead.add(acct)
                if args.verbose:
                    log(f"{acct}: Key/Account nicht nutzbar (HTTP {e.status}: {e}) -> nächster Account")
                continue
            if e.status in (403, 404) and not args.model:
                mark_blocked(acct, model)
                if args.verbose:
                    log(f"{acct}: {model} gesperrt/unbekannt (HTTP {e.status}), nächste Kombination")
                continue
            raise
    limited = [c for c in limited if c[0] not in dead]
    if not limited:
        raise last
    # Alles voll: auf die Kombination warten, die am frühesten wieder frei ist (sofern nicht zu lange).
    # Bei Gleichstand gewinnt die Vorzugsreihenfolge (min() nimmt das erste Minimum).
    st, now = load_state(), time.time()
    acct, key, model = min(limited, key=lambda c: max(now, st.get(f"{c[0]}|{c[2]}", {}).get("until", 0)))
    wait = st.get(f"{acct}|{model}", {}).get("until", 0) - now
    if wait > (70 if getattr(args, "_last_provider", True) else MAX_RETRY_AFTER):
        raise last_limit
    if wait > 0:
        if args.verbose:
            log(f"alle Accounts/Modelle am Limit – warte {wait:.1f}s auf {acct} / {model}")
        time.sleep(wait)
    content, headers = chat(provider, model, key, messages, args, limit, can_switch=False)
    remember_headers(acct, model, headers)
    return acct, model, content, headers


# ---------------------------------------------------------------- Limit-Gedächtnis (prozessübergreifend)

_STATE_LOCK = threading.Lock()


def parse_dur(s):
    """Groq-Zeitangaben wie '7.66s', '2m59.5s', '1h2m', '450ms' -> Sekunden."""
    return sum(float(n) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[u]
               for n, u in re.findall(r"([\d.]+)(ms|h|m|s)", str(s or "")))


def wait_hint(e, default=2.0):
    """Wartezeit aus Retry-After bzw. Groqs 'try again in 1m2.5s'."""
    ra = e.headers.get("retry-after") or e.headers.get("Retry-After")
    try:
        wait = float(ra) if ra else default
    except ValueError:
        wait = default
    m = re.search(r"try again in ((?:[\d.]+(?:ms|h|m|s))+)", str(e))
    if m:
        wait = max(wait, parse_dur(m.group(1)))
    return wait + 0.5


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_slot(acct, model, **vals):
    with _STATE_LOCK:
        now = time.time()
        st = {k: v for k, v in load_state().items() if now - v.get("t", 0) < 86400 or v.get("until", 0) > now}
        st.setdefault(f"{acct}|{model}", {}).update(vals, t=now)
        tmp = f"{STATE_FILE}.{os.getpid()}.tmp"
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(st, f, indent=1)
            os.replace(tmp, STATE_FILE)
        except OSError:  # paralleler Prozess schreibt gerade -> diesmal nicht merken
            try:
                os.remove(tmp)
            except OSError:
                pass


def remember_headers(acct, model, headers):
    """Restbudget aus den x-ratelimit-Headern merken (Groq: *-tokens = pro Minute, *-requests = pro Tag)."""
    h = {k.lower(): v for k, v in (headers or {}).items()}
    now, vals = time.time(), {"until": 0}
    try:
        if "x-ratelimit-remaining-tokens" in h:
            vals["rem_tok"] = int(float(h["x-ratelimit-remaining-tokens"]))
            vals["lim_tok"] = int(float(h.get("x-ratelimit-limit-tokens") or 0)) or None
            vals["tok_reset_at"] = now + parse_dur(h.get("x-ratelimit-reset-tokens"))
        if h.get("x-ratelimit-remaining-requests", "").strip() == "0":
            vals["until"] = now + parse_dur(h.get("x-ratelimit-reset-requests"))
    except ValueError:
        pass
    save_slot(acct, model, **vals)


def est_remaining(s, now):
    """Geschätztes Token-Restbudget jetzt (None = unbekannt/voll). Groq füllt bis tok_reset_at linear auf."""
    rem, reset_at, t = s.get("rem_tok"), s.get("tok_reset_at", 0), s.get("t", 0)
    if rem is None or now >= reset_at:
        return None
    if s.get("lim_tok") and reset_at > t:
        rem += (s["lim_tok"] - rem) * (now - t) / (reset_at - t)
    return rem


def plan(accounts, models, need):
    """Reihenfolge der (account, key, modell, gesperrt)-Versuche: zuerst alles mit genug Budget – Modelle in
    Vorzugsreihenfolge, je Modell der Account mit dem meisten Restbudget vorn –, danach die knappen/gesperrten,
    sortiert nach 'wieder frei ab'. gesperrt=True heißt: laut 429 erst später wieder nutzbar."""
    st, now = load_state(), time.time()
    ready, full = [], []
    for mi, model in enumerate(models):
        group = []
        for ai, (acct, key) in enumerate(accounts):
            s = st.get(f"{acct}|{model}", {})
            rem = est_remaining(s, now)
            locked = s.get("until", 0) > now
            if locked or (rem is not None and rem < need):
                full.append((max(s.get("until", 0), s.get("tok_reset_at", 0)), mi, ai, acct, key, model, locked))
            else:
                group.append((-(rem if rem is not None else 10**9), ai, acct, key, model, False))
        ready += [c[2:] for c in sorted(group)]
    return ready + [c[3:] for c in sorted(full)]


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


def limiter(provider, key, model):
    """Groq & Co. zählen die Limits pro Account und Modell -> eigener Zähler je (Anbieter, Key, Modell)."""
    with _LIMITERS_LOCK:
        if (provider, key, model) not in _LIMITERS:
            c = PROVIDERS[provider]
            _LIMITERS[(provider, key, model)] = Limiter(c["rpm"], c["tpm"])
        return _LIMITERS[(provider, key, model)]


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
        if not limiter(provider, key, model).acquire(est_tokens(messages, args.max_tokens), block=not can_switch):
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
            wait = wait_hint(e, 2.0 * (attempt + 1))  # Groq nennt die genaue Wartezeit im Text
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
    usable = [p for p in chain if p in PROVIDERS and get_accounts(p)]
    for provider in chain:
        args._last_provider = bool(usable) and provider == usable[-1]
        if provider not in PROVIDERS:
            errors.append(f"{provider}: unbekannter Anbieter")
            continue
        accounts = get_accounts(provider, errors)
        if not accounts:
            if not get_key(PROVIDERS[provider]["key"]):
                errors.append(f"{provider}: kein Key ({PROVIDERS[provider]['key']})")
            continue
        try:
            acct, model, content, _ = chat_any(provider, accounts, messages, args)
            if args.verbose:
                log(f"Antwort von {acct} / {model}")
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
        problems = []
        accounts = get_accounts(provider, problems)
        for p in problems:
            name, _, msg = p.partition(": ")
            print(f"{name:<11} {'FEHLER':<8} {msg}")
        if not accounts and not problems:
            print(f"{provider:<11} {'—':<8} kein Key hinterlegt ({cfg['key']})")
        for acct, key in accounts:
            test_account(provider, acct, key, args)


def cmd_status():
    """Gemerktes Restbudget je Account/Modell (ohne Anfrage zu schicken)."""
    st, now = load_state(), time.time()
    for provider in PROVIDERS:
        for acct, _ in get_accounts(provider):
            rows = sorted((k.split("|", 1)[1], v) for k, v in st.items() if k.split("|", 1)[0] == acct)
            if not rows:
                print(f"{acct:<8} noch keine Daten")
            for model, s in rows:
                rem = est_remaining(s, now)
                if s.get("until", 0) > now:
                    txt = f"am Limit, wieder frei in {s['until'] - now:.0f}s"
                elif rem is None:
                    txt = "frei"
                else:
                    txt = f"~{rem:.0f} Tokens übrig, voll in {s['tok_reset_at'] - now:.0f}s"
                print(f"{acct:<8} {model:<24} {txt}")


def test_account(provider, acct, key, args):
    try:
        t0 = time.time()
        _, model, content, headers = chat_any(provider, [(acct, key)],
                                              [{"role": "user", "content": "Antworte nur mit dem Wort: ok"}],
                                              argparse.Namespace(**{**vars(args), "max_tokens": args.max_tokens or 300}),
                                              limit=False)
        dt = time.time() - t0
        unmark_blocked(acct, model)
        print(f"{acct:<11} {'ok':<8} {model}  ({dt:.1f}s, Antwort: {content.strip()[:20]!r})")
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
                    unmark_blocked(acct, m)
                    status.append(f"{m} ok")
                except ApiError as e:
                    if e.status in (403, 404):
                        mark_blocked(acct, m)
                    status.append(f"{m} " + ("GESPERRT" if e.status in (403, 404) else f"HTTP {e.status}"))
            if status:
                print(f"{'':<20}weitere Modelle: " + ", ".join(status))
    except ApiError as e:
        print(f"{acct:<11} {'FEHLER':<8} HTTP {e.status}: {e}" if e.status else f"{acct:<11} {'FEHLER':<8} {e}")


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


def cmd_set_key(name, from_clipboard=False):
    import getpass
    try:
        var = key_var(*parse_acct(name))
    except ValueError as e:
        raise SystemExit(str(e))
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
    ap.add_argument("--status", action="store_true", help="gemerktes Restbudget je Account/Modell anzeigen")
    ap.add_argument("--list-models", metavar="ANBIETER", choices=list(PROVIDERS))
    ap.add_argument("--set-key", metavar="ANBIETER", help="Key verdeckt eingeben und sicher speichern (groq, groq2 = zweiter Account, gemini, …)")
    ap.add_argument("--clipboard", action="store_true", help="mit --set-key: Key aus der Zwischenablage lesen (und sie danach leeren)")
    ap.add_argument("--stdin", action="store_true", help="unbegrenzt auf gepipte Eingabe warten (für langsame Befehle davor)")
    ap.add_argument("--no-stdin", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("-v", "--verbose", action="store_true", help="Anbieter/Modell und Fehler auf stderr ausgeben")
    args = ap.parse_args()

    if args.set_key:
        return cmd_set_key(args.set_key, args.clipboard)
    if args.test:
        return cmd_test(args)
    if args.status:
        return cmd_status()
    if args.list_models:
        accounts = get_accounts(args.list_models)
        for m in list_models(args.list_models, accounts[0][1] if accounts else None, refresh=True):
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
