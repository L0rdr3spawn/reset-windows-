---
name: find-the-needle-save
description: "Find The Needle (Demo, Godot 4.7) Spielstand-Ort, Save-Passwort und PCK-Schlüssel zum Geld-Editieren"
metadata:
  node_type: memory
  type: reference
  originSessionId: 6413fe09-b409-4a09-860c-8dd21269e279
  modified: 2026-09-30T18:15:00.015Z
---

Find The Needle Demo = intern "Haystack Incremental" (Godot 4.7.2).
- Save: `%APPDATA%\Godot\app_userdata\Haystack Incremental\saves\slot_N.dat` (+ `.bak`), GDEC-verschlüsselt (Godot FileAccessEncrypted, AES-256-CFB, Key = md5(pass).hexdigest() als ASCII).
- SAVE_PASS (aus autoload/save_manager.gdc): `b88b32d1fb83a23ac1facd11a612222774cca9aed41a87ed`
- PCK-Schlüssel (encrypted directory, in EXE bei 0x46f4eb0): `a08ab0da1b112e09af5279d1d929e965ce8e7053b3337d194b8a24cdb9eec816`
- Inhalt = store_var-Variant; `money` steht 2× (Slot-Übersicht + state), dazu `money_peak`. Double in-place ersetzen, neu verschlüsseln.
- Spiel vorher schließen (speichert beim Beenden); `profile.cfg` hat nur Statistiken.
- 2026-09-30 Geld auf 100000 gesetzt, Backups in `saves\backup_vor_geld_*`.
