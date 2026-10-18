# Macht die Bose-Earbuds stabiler und verhindert, dass ihr Headset-Mikro je benutzt wird.
#  1. Freisprech-Modus (Hands-Free) der Earbuds abschalten -> kein Headset-Mikro mehr,
#     kein Umschalten Stereo <-> Headset (haeufige Ursache fuer Abbrueche)
#  2. Bluetooth-Adapter darf nicht mehr schlafen (USB-Energiesparen aus)
# Rueckgaengig: bluetooth-rueckgaengig.ps1 im selben Ordner (als Admin).

$ErrorActionPreference = 'Continue'
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$log = Join-Path $PSScriptRoot ("bluetooth-stabil_{0:yyyy-MM-dd_HHmmss}.log" -f (Get-Date))
Start-Transcript -Path $log | Out-Null

Write-Host "`n== 1. Freisprech-Modus der Earbuds abschalten ==" -ForegroundColor Cyan
$hf = Get-PnpDevice | Where-Object {
    ($_.InstanceId -like 'BTHHFENUM\BTHHFPAUDIO\*') -or
    ($_.InstanceId -like 'BTHENUM\{0000111E-0000-1000-8000-00805F9B34FB}*')
} | Where-Object { $_.FriendlyName -match 'Bose|Boooooom' }
foreach ($d in $hf) {
    try {
        Disable-PnpDevice -InstanceId $d.InstanceId -Confirm:$false -ErrorAction Stop
        Write-Host "  aus: $($d.FriendlyName)" -ForegroundColor Green
    } catch { Write-Host "  FEHLER bei $($d.FriendlyName): $_" -ForegroundColor Red }
}

Write-Host "`n== 2. Bluetooth-Adapter wach halten ==" -ForegroundColor Cyan
$bt = Get-PnpDevice -Class Bluetooth | Where-Object { $_.InstanceId -like 'USB\VID_8087*' } | Select-Object -First 1
if ($bt) {
    $key = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($bt.InstanceId)\Device Parameters"
    Set-ItemProperty -Path $key -Name SelectiveSuspendEnabled -Value 0 -Type DWord
    $pm = Get-CimInstance -Namespace root\wmi -ClassName MSPower_DeviceEnable |
        Where-Object { $_.InstanceName -like "$($bt.InstanceId)*" }
    foreach ($p in $pm) { $p | Set-CimInstance -Property @{ Enable = $false } }
    Write-Host "  $($bt.FriendlyName): Energiesparen aus" -ForegroundColor Green
} else { Write-Host "  Intel-Bluetooth-Adapter nicht gefunden" -ForegroundColor Red }

# USB-Energiesparen (selektives Aussetzen) im aktuellen Energieplan aus
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setactive SCHEME_CURRENT
Write-Host "  USB-Energiesparen im Energieplan: aus" -ForegroundColor Green

Write-Host "`nFertig. Earbuds einmal in die Ladeschale und wieder raus (neu verbinden)." -ForegroundColor Yellow
Write-Host "Ab dem naechsten Neustart greift auch das Adapter-Energiesparen sicher." -ForegroundColor Yellow
Stop-Transcript | Out-Null
Read-Host "`nEnter zum Schliessen"
