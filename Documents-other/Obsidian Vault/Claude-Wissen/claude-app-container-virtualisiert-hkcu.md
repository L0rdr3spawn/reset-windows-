---
name: claude-app-container-virtualisiert-hkcu
description: "Befehle aus der Claude-Desktop-App laufen im MSIX-Container – HKCU-Schreibzugriffe und neue AppData-Dateien landen in einer privaten Kopie, nicht im echten Profil"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 897e51a7-2859-4c70-8137-7463f9a0442d
  modified: 2026-10-01T14:48:11.159Z
---

Die Claude-Desktop-App ist ein MSIX-Paket (`Claude_pzs8sxrjxfjjc`). Alles, was Bash/PowerShell-Tools
starten, läuft in deren Container: **Schreiben/Löschen in HKCU wirkt nur in der Paket-Hive**
(`%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\SystemAppData\Helium\User.dat`), neue Dateien unter
AppData landen in `...\LocalCache\Local|Roaming`. Lesen zeigt danach die eigene, falsche Sicht –
auch mit `dangerouslyDisableSandbox`. Echt sind dagegen: Löschen vorhandener Dateien, Prozesse,
geplante Tasks, HKLM (elevated), Dateien außerhalb von AppData.

**Why:** Am 2026-10-01 schien Opera/Yandex „deinstalliert“, in der echten Registry standen aber
Uninstall-Einträge, Autostarts und ProgIDs noch – aufgefallen nur, weil `winget list` (läuft
außerhalb) etwas anderes zeigte als `reg query`.

**How to apply:** Für alles, was HKCU oder AppData wirklich ändern oder prüfen soll, Skript in den
Arbeitsordner (nicht AppData) schreiben und außerhalb starten:
`Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<pfad>"'}`,
Ausgabe in eine Datei umleiten und zurücklesen. Skriptdateien nur ASCII (PS 5.1 liest UTF-8 ohne
BOM als ANSI). Widerspruch zwischen zwei Quellen = erst Virtualisierung verdächtigen.
Siehe [[nur-brave-als-browser]].
