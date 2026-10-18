# Installiert alles aus vorschlaege.txt, was NICHT mit # beginnt.
# Vorher die Datei durchsehen und unerwuenschte Zeilen mit # auskommentieren.
#   powershell -ExecutionPolicy Bypass -File install-optional.ps1   (als Administrator)

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrator')) {
    Write-Host 'Bitte als Administrator starten.' -ForegroundColor Red; exit 1
}
$list = Join-Path $PSScriptRoot 'vorschlaege.txt'
$failed = @()
foreach ($line in Get-Content $list -Encoding UTF8) {
    if ($line -match '^\s*#' -or $line -notmatch '\|') { continue }
    $id = ($line -split '\|')[0].Trim()
    Write-Host ">> $id" -ForegroundColor Cyan
    winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) { $failed += $id }
}
if ($failed) { Write-Host "`nFehlgeschlagen:" -ForegroundColor Yellow; $failed }
