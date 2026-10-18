"""Setzt Handys Einstellungen fuer: Ctrl+Win = Diktat mit lokalem KI-Aufraeumen, alles auf der RTX 3050.
Aufruf: python handy-einstellen.py <settings_store.json> [modell-id]
Handy muss dabei beendet sein (sonst ueberschreibt es die Datei)."""
import json
import os
import sys

DATEI = sys.argv[1]
MODELL = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
HIER = os.path.dirname(os.path.abspath(__file__))
PROMPT_ID = "diktat_de_en_lokal"

# Stabile Kennung der RTX 3050 (PCI-Adresse aus nvidia-smi 00000000:05:00.0), Format wie Handy sie speichert
GPU_3050 = json.dumps(["vulkan", "id", "0000:05:00.0"], separators=(",", ":"))

with open(DATEI, encoding="utf-8") as f:
    daten = json.load(f)
s = daten["settings"] if isinstance(daten.get("settings"), dict) else daten

# 1) Autostart, versteckt starten, Modell im Speicher halten (schnell)
s["autostart_enabled"] = True
s["start_hidden"] = True
s["model_unload_timeout"] = "never"

# 2) Spracherkennung fest auf der RTX 3050 (gilt fuer jedes GGUF-Modell, auch nach Modellwechsel)
s["transcribe_accelerator"] = "gpu"
s["transcribe_gpu_device"] = GPU_3050
if MODELL:
    s["selected_model"] = MODELL
    s["selected_language"] = "auto"

# 3) Tastenkuerzel: Ctrl+Win = Diktat MIT Aufraeumen, Ctrl+Shift+Leertaste = rohes Diktat
b = s["bindings"]
b["transcribe_with_post_process"]["current_binding"] = "ctrl_left+super_left"
b["transcribe"]["current_binding"] = "ctrl+shift+space"

# 4) Aufraeumen ueber den lokalen llama.cpp-Server (Port 8091, Qwen3-4B auf der 3050)
s["post_process_enabled"] = True
s["post_process_provider_id"] = "custom"
for p in s["post_process_providers"]:
    if p.get("id") == "custom":
        p["base_url"] = "http://127.0.0.1:8091/v1"
s.setdefault("post_process_models", {})["custom"] = "qwen3-4b"
with open(os.path.join(HIER, "prompt.txt"), encoding="utf-8") as f:
    prompt = f.read()
prompts = [p for p in s.get("post_process_prompts", []) if p.get("id") != PROMPT_ID]
prompts.append({"id": PROMPT_ID, "name": "Diktat DE/EN (lokal, 3050)", "prompt": prompt})
s["post_process_prompts"] = prompts
s["post_process_selected_prompt_id"] = PROMPT_ID

tmp = DATEI + ".neu"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(daten, f, ensure_ascii=False, indent=2)
os.replace(tmp, DATEI)

print(f"Autostart: an, versteckt: an, Modell bleibt geladen")
print(f"Spracherkennung: GPU fest = RTX 3050 ({GPU_3050}), Modell = {s['selected_model']}, Sprache = {s['selected_language']}")
print(f"Ctrl+Win = Diktat + Aufraeumen | Ctrl+Shift+Leertaste = rohes Diktat")
print(f"Aufraeumen: lokal http://127.0.0.1:8091/v1 (qwen3-4b), Prompt '{PROMPT_ID}'")
