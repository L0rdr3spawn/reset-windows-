---
name: steam-mydayz-tool
description: Selbstgebautes Steam-Account-Wechsel- + MyDayZ-Starttool in C:\Users\reiss\Documents\claude
metadata: 
  node_type: memory
  type: project
  originSessionId: a94dbafe-12db-4683-81be-fd4f114a9470
  modified: 2026-08-28T02:17:58.722Z
---

Tool `steam-switch.ps1` (+ `Steam-Account.cmd`, `MyDayZ.cmd`) in `C:\Users\reiss\Documents\claude`.

**Steam-Account-Wechsel:** Die Registry `AutoLoginUser` reicht bei der aktuellen Steam-Version NICHT — Steam zeigt dann den "Who's playing?"-Picker und loggt nichts ein. Verlaesslich ist `steam.exe -login <AccountName>` (nutzt gespeicherten Token, kein Passwort). Empirisch getestet 2026-08-28.

Accounts/Aliase (steam-aliases.json): l0rdr3spawn=cs2, gooner_master_1000=smurf, felixreissen@firemail.de=main. main besitzt DayZ.

**MyDayZ (steam-mydayz.json):** Server `37.187.143.55:2302:27016`, Profil `L0rdr3spawn`, 30 Mods in fester Reihenfolge. Start umgeht den DZSA Launcher (dessen Suche + Mod-Update sind laut Nutzer verbuggt): `steam -applaunch 221100 -connect=... -nolauncher -name=... -mod=<!dzsal-Junction-Pfade>`. Mod-Ordnernamen mit `[ ]` brauchen `Test-Path -LiteralPath`.

Update-Bug-Strategie: Mods im Steam-Workshop (Account main) abonnieren -> Steam haelt sie selbst aktuell.
