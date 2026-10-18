# Macht bluetooth-stabil.ps1 rueckgaengig (Freisprech-Modus wieder an, Energiesparen wieder an).
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}
Get-PnpDevice | Where-Object {
    ($_.InstanceId -like 'BTHHFENUM\BTHHFPAUDIO\*') -or
    ($_.InstanceId -like 'BTHENUM\{0000111E-0000-1000-8000-00805F9B34FB}*')
} | Where-Object { $_.FriendlyName -match 'Bose|Boooooom' } | ForEach-Object {
    Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false; Write-Host "an: $($_.FriendlyName)"
}
$bt = Get-PnpDevice -Class Bluetooth | Where-Object { $_.InstanceId -like 'USB\VID_8087*' } | Select-Object -First 1
if ($bt) {
    Remove-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Enum\$($bt.InstanceId)\Device Parameters" -Name SelectiveSuspendEnabled -ErrorAction SilentlyContinue
    Get-CimInstance -Namespace root\wmi -ClassName MSPower_DeviceEnable | Where-Object { $_.InstanceName -like "$($bt.InstanceId)*" } |
        ForEach-Object { $_ | Set-CimInstance -Property @{ Enable = $true } }
}
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1
powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1
powercfg /setactive SCHEME_CURRENT
Read-Host "Rueckgaengig gemacht. Enter zum Schliessen"
