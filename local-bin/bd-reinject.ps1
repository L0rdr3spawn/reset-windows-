# Haelt BetterDiscord nach Discord-Updates aktiv: patcht discord_desktop_core/index.js
# jeder app-* Version, sobald sie unpatched ist. Laeuft als Aufgabe "BetterDiscord-Reinject"
# (bei Anmeldung, Schleife alle 30 s, sehr billig). Einmalig: -Once
param([switch]$Once)

$asar  = Join-Path $env:APPDATA 'BetterDiscord\data\betterdiscord.asar'
$base  = Join-Path $env:LOCALAPPDATA 'Discord'
$asarJs = $asar.Replace('\','\\')
$content = "require(`"$asarJs`");`nmodule.exports = require('./core.asar');`n"

function Patch-All {
    if (-not (Test-Path $asar)) { return }
    foreach ($app in Get-ChildItem $base -Directory -Filter 'app-*' -ErrorAction SilentlyContinue) {
        $mods = Join-Path $app.FullName 'modules'
        foreach ($core in Get-ChildItem $mods -Directory -Filter 'discord_desktop_core-*' -ErrorAction SilentlyContinue) {
            $idx = Join-Path $core.FullName 'discord_desktop_core\index.js'
            if (-not (Test-Path $idx)) { continue }
            $cur = Get-Content $idx -Raw -ErrorAction SilentlyContinue
            if ($cur -and $cur.Contains('BetterDiscord')) { continue }
            try { [IO.File]::WriteAllText($idx, $content, (New-Object Text.UTF8Encoding $false)) } catch { }
        }
    }
}

# Discord auf die stromsparende GPU (iGPU) legen, damit es die NVIDIA-Karten nicht weckt.
# Der Pfad enthaelt die app-Version, deshalb hier mitgepflegt.
function Set-GpuPref {
    $key = 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences'
    $latest = Get-ChildItem $base -Directory -Filter 'app-*' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if (-not $latest) { return }
    $exe = Join-Path $latest.FullName 'Discord.exe'
    if (-not (Test-Path $key)) { New-Item $key -Force | Out-Null }
    $cur = (Get-ItemProperty $key -Name $exe -ErrorAction SilentlyContinue).$exe
    if ($cur -ne 'GpuPreference=1;') { Set-ItemProperty $key -Name $exe -Value 'GpuPreference=1;' -Type String }
    # alte Discord-Versionen aufraeumen
    $prefix = Join-Path $base 'app-'
    foreach ($n in (Get-Item $key).Property) { if ($n.StartsWith($prefix) -and $n -ne $exe) { Remove-ItemProperty $key -Name $n -ErrorAction SilentlyContinue } }
}

if ($Once) { Patch-All; Set-GpuPref; return }
$tick = 0
while ($true) { Patch-All; if ($tick % 20 -eq 0) { Set-GpuPref }; $tick++; Start-Sleep -Seconds 30 }
