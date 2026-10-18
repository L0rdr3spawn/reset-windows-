---
name: seelen-ui-review
description: "Seelen UI (eythaann/Seelen-UI) geklont nach claude/seelen-ui; ~30 Bugfixes uncommitted, voll verifiziert; Toolchain jetzt installiert"
metadata:
  node_type: memory
  type: project
  originSessionId: 284f4345-aae6-483d-9d96-6bc3c32ded70
  modified: 2026-09-30T15:30:00.722Z
---

Seelen UI flach geklont (Stand ad4e37f, 2026-09-29) nach `C:\Users\reiss\Documents\claude\seelen-ui`, in `.gitignore` des claude-Repos.
User wählte „echte Bugs zuerst“, Umbau nur punktuell, Upstream-kompatibel bleiben. Stand 2026-09-30: Fixes committed auf Branch `fix/code-review` (8c44dca, 28e131e, 7b3b481).

Toolchain installiert (User-Zustimmung 2026-09-29): VS 2022 Build Tools (MSVC 14.44), rustup + nightly-2026-05-22 (clippy, rustfmt), Deno via winget (nicht im PATH), npm ci gelaufen (lefthook-Hooks im Klon aktiv). `.cargo\bin` seit 2026-09-30 im User-PATH. In der User-PowerShell ist `npm.ps1` per Execution Policy blockiert → `npm.cmd` benutzen.
Verifizieren mit: `export PATH="$HOME/.cargo/bin:$LOCALAPPDATA/Microsoft/WinGet/Packages/DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe:$PATH"`, dann `cargo fmt --all -- --check`, `cargo clippy --locked --workspace --all-targets -- -D warnings`, `cargo test --locked --workspace`, `npx tsc --noEmit`, `npx svelte-check`, `deno lint`, `deno fmt --check`, `cd libs/core && deno test -A`, `npm run build:ui`. Alles grün.

Kein Konsolenfenster mehr (2026-09-30): `windows_subsystem` jetzt auch im Debug, Konsole nur mit `--features console` (uncommitted auf Branch fix/code-review). Dienst-Task `\Seelen\Seelen UI Service` zeigt auf target\debug\slu-service.exe --startup.

Starten (2026-09-30, User hat es selbst gewollt): Debug-Exe lädt Widgets von `http://localhost:3579` (devUrl). Ohne laufenden Dev-Server (`npx tsx scripts/build.ts --serve` bzw. `npm run tauri dev`) → alle Widgets „reagierte zu oft nicht mehr“ (Liveness-Fehler). Alternative ohne Server: `cargo build --features custom-protocol`. Dienst slu-service lief nicht → native Taskleiste bleibt, Shortcuts fehlen (Start braucht UAC).

VORFALL 2026-09-30: Nach Neustart startete der Autostart-Task den Debug-Dienst → Windows-Taskleiste ausgeblendet, Seelen-Widgets ohne Dev-Server tot → User hatte gar keine Taskleiste. Behoben: Prozesse beendet, `target\debug\slu-service.exe` → `slu-service.exe.deaktiviert` umbenannt (Task-Deaktivieren braucht Admin, UAC-Versuch griff nicht). Jeder `cargo build` erzeugt slu-service.exe neu → Task wäre wieder scharf! Debug-Build NIE per Autostart laufen lassen.

Feste Installation (2026-09-30, User will Autostart „wie andere Apps“): Build mit eingebauter UI nach `target\local\debug` (Befehle im Kopf von `scripts\install-local.ps1`), Skript kopiert nach `C:\Program Files\Seelen UI` + `slu-service install` + Task starten. Code-Patches: Signaturprüfung (checksums.rs) und Updater (updater.rs) bei `debug_assertions` aus. Skript muss der User selbst als Admin starten (Classifier blockt UAC-Start durch Claude). Stand 2026-10-01: installiert, Task zeigt auf Program Files, Seelen läuft von dort (Dock+Toolbar sichtbar); Neustart-Test steht aus. Offen: per Task/Explorer gestartete GUI-Builds schreiben nichts in die Logdateien (CLI-Aufruf schon) – Ursache ungeklärt. ACHTUNG: `tauri dev` startet den Dienst aus target\debug, der biegt den Task wieder auf den Debug-Build um → danach install-local.ps1 erneut.

**Why:** Dienst nie gestartet — ersetzt Taskleiste/Desktop und der Dienst legt geplante Aufgabe mit höchsten Rechten an; nur mit ausdrücklichem OK starten.
**How to apply:** Offene Hinweise (nicht gefixt): MSIX-Task zeigt auf beschreibbares WindowsApps-Alias (UAC-Bypass), Manager-LazyLocks mit expect, Drittanbieter-Widgets können fast alle Befehle ohne Nachfrage aufrufen, WM-Reservierung evtl. durch SystemForeground abgebrochen.
