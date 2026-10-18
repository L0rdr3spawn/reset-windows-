# Setzt eine OLED-artige Tonkurve (Gamma-Ramp) nur auf dem 2. Monitor.
#   -Gamma      Ziel-Gamma (2.2 = neutral, 2.4 = tiefere Schatten, OLED-typisch)
#   -BlackCrush Anteil der dunkelsten Toene, der auf Schwarz gezogen wird (0.0 - 0.05)
#   -Reset      Stellt die lineare Standardkurve wieder her
param([double]$Gamma = 2.4, [double]$BlackCrush = 0.012, [string]$Device = "DISPLAY2", [switch]$Reset)

# Im Regler gespeicherte Werte verwenden (einstellungen.json), sofern nichts explizit uebergeben wurde
$cfgPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "einstellungen.json"
if ((Test-Path $cfgPath) -and -not $PSBoundParameters.ContainsKey('Gamma')) {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
    $Gamma = $cfg.Gamma; $BlackCrush = $cfg.BlackCrush / 100.0
}

Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public class Ramp {
  [DllImport("gdi32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr CreateDC(string drv, string dev, string o, IntPtr i);
  [DllImport("gdi32.dll")] public static extern bool DeleteDC(IntPtr dc);
  [DllImport("gdi32.dll")] public static extern bool SetDeviceGammaRamp(IntPtr dc, ushort[] ramp);
  public static bool Apply(string dev, ushort[] ramp) {
    IntPtr dc = CreateDC(null, @"\\.\" + dev, null, IntPtr.Zero);
    if (dc == IntPtr.Zero) return false;
    bool ok = SetDeviceGammaRamp(dc, ramp); DeleteDC(dc); return ok;
  }
}
"@

$ramp = New-Object 'uint16[]' 768
for ($i = 0; $i -lt 256; $i++) {
    $x = $i / 255.0
    if ($Reset) { $y = $x } else {
        # Schwarz-Crush: die untersten Prozent werden zu echtem Schwarz
        $x2 = [Math]::Max(0.0, ($x - $BlackCrush) / (1.0 - $BlackCrush))
        # Gamma relativ zur nativen 2.2-Kurve des Panels
        $y = [Math]::Pow($x2, $Gamma / 2.2)
    }
    $v = [uint16][Math]::Min(65535, [Math]::Round($y * 65535))
    $ramp[$i] = $v; $ramp[$i + 256] = $v; $ramp[$i + 512] = $v
}

if ([Ramp]::Apply($Device, $ramp)) {
    if ($Reset) { "Gamma auf $Device zurueckgesetzt." } else { "Gamma $Gamma / BlackCrush $BlackCrush auf $Device gesetzt." }
} else {
    "FEHLER: Windows hat die Kurve abgelehnt (evtl. zu stark)."
    exit 1
}
