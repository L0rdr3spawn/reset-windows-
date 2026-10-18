# Handy einrichten - per Doppelklick auf "Handy reparieren.cmd" (Desktop) starten, NICHT aus Claude heraus.
# Ctrl+Win = Diktat + lokales KI-Aufraeumen, Spracherkennung und Aufraeumen fest auf der RTX 3050, Autostart fuer beides.
param([string]$Modell = '')
$ErrorActionPreference = 'Stop'
$cfg  = "$env:APPDATA\com.pais.handy\settings_store.json"
$exe  = "$env:LOCALAPPDATA\Handy\handy.exe"
$auf  = "$env:USERPROFILE\handy-aufraeumer"
$bak  = $PSScriptRoot
$run  = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'

function Schritt($t) { Write-Host "`n>> $t" -ForegroundColor Cyan }

foreach ($p in $exe, $cfg, "$auf\start-aufraeumer.ps1", "$auf\handy-einstellen.py") {
    if (-not (Test-Path $p)) { throw "Nicht gefunden: $p" }
}

Schritt "Handy und alten Aufraeumer beenden"
Get-Process handy, llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
"ok"

Schritt "Sicherung der Einstellungen"
$ziel = Join-Path $bak ("settings_store.json." + (Get-Date -f 'yyyy-MM-dd_HHmmss'))
Copy-Item $cfg $ziel
"gesichert nach $ziel"

Schritt "Einstellungen setzen"
& python "$auf\handy-einstellen.py" $cfg $Modell
if ($LASTEXITCODE -ne 0) { throw "Einstellungen konnten nicht gesetzt werden - Sicherung liegt in $ziel" }

Schritt "Autostart fuer den KI-Aufraeumer"
$cmd = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$auf\start-aufraeumer.ps1`""
New-ItemProperty -Path $run -Name 'Handy-Aufraeumer' -Value $cmd -PropertyType String -Force | Out-Null
"eingetragen"

Schritt "KI-Aufraeumer starten (RTX 3050)"
& powershell -NoProfile -ExecutionPolicy Bypass -File "$auf\start-aufraeumer.ps1"
$bereit = $false
foreach ($i in 1..60) { try { Invoke-RestMethod http://127.0.0.1:8091/health -TimeoutSec 2 | Out-Null; $bereit = $true; break } catch { Start-Sleep 1 } }
if ($bereit) { "laeuft" } else { Write-Host "startet NICHT - siehe $auf\aufraeumer.log" -ForegroundColor Red }

Schritt "Handy starten"
Start-Process $exe
Start-Sleep 8
if (Get-Process handy -ErrorAction SilentlyContinue) { "Handy laeuft" } else { Write-Host "Handy laeuft NICHT" -ForegroundColor Red }

Schritt "Windows-Autostart fuer Handy pruefen"
$eintrag = (Get-ItemProperty $run).PSObject.Properties | Where-Object { $_.Value -is [string] -and $_.Value -match 'handy\.exe' }
if ($eintrag) { "Handy hat sich selbst eingetragen: $($eintrag.Name)" }
else {
    New-ItemProperty -Path $run -Name 'Handy' -Value "`"$exe`"" -PropertyType String -Force | Out-Null
    "Eintrag selbst angelegt: Handy"
}

Write-Host "`nFertig." -ForegroundColor Green
Write-Host "Ctrl+Win gedrueckt halten (oder antippen) = Diktat + KI-Aufraeumen"
Write-Host "Ctrl+Shift+Leertaste = Diktat ohne Aufraeumen"
Write-Host "Beides startet ab jetzt automatisch mit Windows."
