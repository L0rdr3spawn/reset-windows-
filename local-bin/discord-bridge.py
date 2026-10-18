#!/usr/bin/env python3
"""Client fuer das BetterDiscord-Plugin ClaudeBridge (Datei-Warteschlange).

  discord-bridge status|guilds|dms|unread|debug
  discord-bridge channels GUILD_ID
  discord-bridge messages CHANNEL_ID [--limit N] [--before ID] [--after ID]
  discord-bridge files CHANNEL_ID [--limit N]
  discord-bridge search "text" (--guild ID | --channel ID)
  discord-bridge download URL --confirm      (nur nach Ruecksprache mit dem User)
  discord-bridge mode CHANNEL_ID [--set auto|manual]   (Standard manual; auto nur nach Klick des Users im Fenster)
  discord-bridge delete CHANNEL_ID --message MSG_ID --confirm   (nur EIGENE Nachrichten, User klickt in Discord)
  discord-bridge send CHANNEL_ID --text "..." [--reply-to MSG_ID] --confirm   (NUR nach ausdruecklichem OK des Users zu Text+Ziel)

Discord (mit BetterDiscord + Plugin) muss laufen.
"""
import argparse, json, os, sys, time, uuid

D = os.path.join(os.path.expanduser("~"), ".config", "discord-bridge")
REQ, RES = os.path.join(D, "req"), os.path.join(D, "res")

p = argparse.ArgumentParser(add_help=True)
p.add_argument("op", choices=["status", "guilds", "channels", "dms", "unread", "messages", "files", "search", "download", "send", "delete", "mode", "debug"])
p.add_argument("target", nargs="?")
p.add_argument("--limit", type=int)
p.add_argument("--before"); p.add_argument("--after")
p.add_argument("--guild"); p.add_argument("--channel")
p.add_argument("--confirm", action="store_true")
p.add_argument("--message"); p.add_argument("--set"); p.add_argument("--text"); p.add_argument("--reply-to", dest="reply_to")
p.add_argument("--timeout", type=int, default=None)
a = p.parse_args()
if a.timeout is None:
    a.timeout = 140 if a.op in ("send", "delete", "mode") else 30  # send wartet auf den Klick des Users in Discord (bis 120 s)

req = {"op": a.op}
if a.op == "channels": req["guild"] = a.target
elif a.op in ("messages", "files"): req["channel"] = a.target
elif a.op == "search": req["q"] = a.target; req["guild"] = a.guild; req["channel"] = a.channel
elif a.op == "send": req["channel"] = a.target; req["content"] = a.text; req["reply_to"] = a.reply_to; req["confirm"] = a.confirm
elif a.op == "mode": req["channel"] = a.target; req["set"] = a.set
elif a.op == "delete": req["channel"] = a.target; req["message"] = a.message; req["confirm"] = a.confirm
elif a.op == "download": req["url"] = a.target; req["confirm"] = a.confirm
for k in ("limit", "before", "after"):
    if getattr(a, k) is not None: req[k] = getattr(a, k)

os.makedirs(REQ, exist_ok=True); os.makedirs(RES, exist_ok=True)
rid = uuid.uuid4().hex[:16]
tmp = os.path.join(REQ, rid + ".tmp")
with open(tmp, "w", encoding="utf-8") as f: json.dump(req, f)
os.replace(tmp, os.path.join(REQ, rid + ".json"))

out = os.path.join(RES, rid + ".json")
end = time.time() + a.timeout
while time.time() < end:
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f: r = json.load(f)
        os.remove(out)
        if r["ok"]:
            sys.stdout.reconfigure(encoding="utf-8")
            print(json.dumps(r["data"], ensure_ascii=False, indent=2)); sys.exit(0)
        print("FEHLER:", r["error"], file=sys.stderr); sys.exit(1)
    time.sleep(0.3)
try: os.remove(os.path.join(REQ, rid + ".json"))
except OSError: pass
print("Keine Antwort: laeuft Discord mit BetterDiscord und aktivem Plugin ClaudeBridge?", file=sys.stderr); sys.exit(2)
