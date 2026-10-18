# Traegt in die Prism-Instanzen ein, dass vor jedem Start die Master-Einstellungen eingespielt
# und nach dem Beenden zurueckgesichert werden (siehe sync-options.ps1).
# Wartet vorher, bis Prism zu ist, weil Prism seine Instanz-Einstellungen sonst wieder ueberschreibt.
$ErrorActionPreference = 'Stop'
$log = Join-Path $PSScriptRoot 'install-prism-hooks.log'

while (Get-Process -Name prismlauncher -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }

$instances = @('26.3', '26.2', '26.2(1)', 'Upgrader 1.21.11', 'Gambling addiction - Casino+ Pack', 'All the Mods 10 - ATM10')
$script = 'C:/Users/reiss/Documents/claude/mc-settings/sync-options.ps1'
$wanted = [ordered]@{
    'OverrideCommands' = 'true'
    'PreLaunchCommand' = "powershell -NoProfile -ExecutionPolicy Bypass -File $script apply"
    'PostExitCommand'  = "powershell -NoProfile -ExecutionPolicy Bypass -File $script save"
}
$utf8 = New-Object System.Text.UTF8Encoding($false)

foreach ($name in $instances) {
    $cfg = Join-Path $env:APPDATA "PrismLauncher\instances\$name\instance.cfg"
    if (-not (Test-Path -LiteralPath $cfg)) { Add-Content $log "fehlt: $name"; continue }

    Copy-Item -LiteralPath $cfg -Destination "$cfg.vor-settings-sync" -Force
    $lines = [Collections.Generic.List[string]]([IO.File]::ReadAllLines($cfg, $utf8))

    foreach ($key in $wanted.Keys) {
        $index = $lines.FindIndex({ param($l) $l.StartsWith("$key=") })
        $entry = "$key=$($wanted[$key])"
        # Neue Schluessel direkt unter [General], nicht ans Dateiende in einen anderen Abschnitt.
        if ($index -ge 0) { $lines[$index] = $entry } else { $lines.Insert($lines.IndexOf('[General]') + 1, $entry) }
    }

    [IO.File]::WriteAllLines($cfg, $lines, $utf8)
    Add-Content $log "$(Get-Date -Format s) eingetragen: $name"
}
