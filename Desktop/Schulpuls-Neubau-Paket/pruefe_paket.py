"""Prüft das Neubau-Paket: Definitionen/Verweise der Anforderungs-Kennungen, Abnahme-Zeilen, Marker, Geheimnisse."""
import re, sys, glob, os, collections

PAKET = sys.argv[1] if len(sys.argv) > 1 else "paket"
ID = re.compile(r"\b([A-Z]{3})-(\d{3})\b")
# Definition: Kennung steht am Zeilenanfang (nach Markdown-Zeichen), z. B. "### STP-001 ·", "**SIC-001** ·", "- **REC-001**"
DEF = re.compile(r"^([A-Z]{3}-\d{3})\b(?!\s*(?:bis|ff))")
STRIP = " \t#>*-|"
PREFIXES = set("DSG STP VER KLB NOT KUR NAC FOR STA LEH SCH REC ANM DAT BEN INT BET OBE SIC REH QUA PRI DAM".split())

defs = collections.defaultdict(list)   # id -> [(datei, zeile)]
refs = collections.defaultdict(list)
files = sorted(glob.glob(os.path.join(PAKET, "*.md")))
report = []
for f in files:
    name = os.path.basename(f)
    lines = open(f, encoding="utf-8").read().split("\n")
    n_def = n_abn = 0
    cur = None
    for i, line in enumerate(lines, 1):
        m = DEF.match(line.lstrip(STRIP))
        if m and m.group(1).split("-")[0] in PREFIXES:
            defs[m.group(1)].append((name, i))
            n_def += 1
        for m2 in ID.finditer(line):
            if m2.group(1) in PREFIXES:
                refs[m2.group(0)].append((name, i))
        if re.match(r"^\s*[-*]?\s*\**Abnahme", line):
            n_abn += 1
    text = "\n".join(lines)
    markers = re.findall(r"<!--\s*([A-ZÄÖÜ\-0-9 ]+?)\s*-->", text)
    report.append((name, len(lines), n_def, n_abn, markers))

print("== Dateien: Zeilen | Definitionen | Abnahme-Zeilen | Marker")
for name, nl, nd, na, mk in report:
    print(f"{name:55s} {nl:6d} {nd:5d} {na:5d}  {mk}")

print("\n== Kennungen, die mehrfach definiert sind (je Datei-Paar)")
dup = {k: v for k, v in defs.items() if len(v) > 1}
by_pair = collections.Counter()
for k, v in dup.items():
    by_pair[tuple(sorted(set(x[0] for x in v)))] += 1
for pair, c in by_pair.most_common():
    print(c, pair)
print("Beispiele:", list(dup.items())[:5])

print("\n== Verwiesen, aber nirgends definiert")
missing = collections.defaultdict(list)
for k, v in refs.items():
    if k not in defs:
        missing[k] = v
print(len(missing), "Kennungen")
bykind = collections.Counter(k.split("-")[0] for k in missing)
print(dict(bykind))
for k in sorted(missing)[:60]:
    print(" ", k, "<-", ", ".join(sorted(set(f"{a}:{b}" for a, b in missing[k][:3]))))

print("\n== Anzahl Definitionen je Kürzel")
cnt = collections.Counter(k.split("-")[0] for k in defs)
print(dict(sorted(cnt.items())))
