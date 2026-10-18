# Haelt Tastenbelegung, Empfindlichkeit, FOV, Lautstaerken usw. ueber alle Prism-Instanzen gleich.
#
#   sync-options.ps1 apply [mcDir]   Master-Einstellungen in <mcDir>\options.txt einspielen (Prism: vor dem Start)
#   sync-options.ps1 save  [mcDir]   Einstellungen aus <mcDir>\options.txt in den Master uebernehmen (Prism: nach dem Beenden)
#
# Ohne mcDir wird $env:INST_MC_DIR benutzt, das Prism beim Pre-Launch/Post-Exit-Befehl setzt.
param(
    [Parameter(Mandatory = $true)][ValidateSet('apply', 'save')][string]$Mode,
    [string]$McDir = $env:INST_MC_DIR
)

$ErrorActionPreference = 'Stop'
$master = Join-Path $PSScriptRoot 'settings.txt'
$utf8 = New-Object System.Text.UTF8Encoding($false)

# Welche Zeilen aus options.txt zum "persoenlichen Setup" gehoeren.
$synced = '^(key_.+|soundCategory_.+|mouseSensitivity|fov|fovEffectScale|gamma|guiScale|rawMouseInput|invertYMouse|invertXMouse|toggleCrouch|toggleSprint|toggleAttack|toggleUse|autoJump|mouseWheelSensitivity|discrete_mouse_scroll|renderDistance|simulationDistance|maxFps|enableVsync|entityDistanceScaling|chatScale|chatOpacity|showSubtitles|damageTiltStrength|screenEffectScale|darknessEffectScale|glintSpeed|glintStrength)$'

function Read-Options([string]$path) {
    $map = [ordered]@{}
    if (Test-Path -LiteralPath $path) {
        foreach ($line in [IO.File]::ReadAllLines($path, $utf8)) {
            $i = $line.IndexOf(':')
            if ($i -gt 0) { $map[$line.Substring(0, $i).TrimStart([char]0xFEFF)] = $line.Substring($i + 1) }
        }
    }
    return $map
}

function Write-Options([string]$path, $map) {
    $lines = foreach ($k in $map.Keys) { "${k}:$($map[$k])" }
    # Erst in eine Temp-Datei, dann ersetzen: ein Abbruch mitten im Schreiben hinterlaesst keine halbe Datei.
    $tmp = "$path.tmp"
    [IO.File]::WriteAllLines($tmp, [string[]]@($lines), $utf8)
    if (Test-Path -LiteralPath $path) { [IO.File]::Replace($tmp, $path, [NullString]::Value) } else { [IO.File]::Move($tmp, $path) }
}

if (-not $McDir) { throw 'Kein Minecraft-Ordner (weder Parameter noch INST_MC_DIR).' }
$options = Join-Path $McDir 'options.txt'
# Neue Instanz ohne options.txt: nichts einspielen (ohne "version"-Zeile laesst Minecraft alte Datenfixer
# ueber die Tasten laufen) und nach dem Beenden die Standardwerte nicht in den Master uebernehmen.
$fresh = Join-Path $McDir '.settings-sync-neu'

# Mehrere Instanzen koennen gleichzeitig starten/enden -> Master nur nacheinander lesen/schreiben.
$mutex = New-Object System.Threading.Mutex($false, 'Local\mc-settings-sync')
try { [void]$mutex.WaitOne(30000) } catch [System.Threading.AbandonedMutexException] { }
try {
if ($Mode -eq 'apply') {
    if (-not (Test-Path -LiteralPath $master)) { exit 0 }
    if (-not (Test-Path -LiteralPath $options)) { [IO.File]::WriteAllText($fresh, ''); exit 0 }
    $target = Read-Options $options
    $source = Read-Options $master
    foreach ($k in $source.Keys) { $target[$k] = $source[$k] }
    # Keine Willkommens-/Barrierefreiheits-Seite, die den direkten Serverbeitritt blockiert.
    $target['onboardAccessibility'] = 'false'
    Write-Options $options $target
}
else {
    if (Test-Path -LiteralPath $fresh) { Remove-Item -LiteralPath $fresh; exit 0 }
    if (-not (Test-Path -LiteralPath $options)) { exit 0 }
    $current = Read-Options $options
    $keep = Read-Options $master
    foreach ($k in $current.Keys) { if ($k -match $synced) { $keep[$k] = $current[$k] } }
    Write-Options $master $keep
}
}
finally { try { $mutex.ReleaseMutex() } catch { } }
