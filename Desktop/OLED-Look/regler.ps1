# Live-Regler fuer den 2. Monitor (INNOCN 44C1G, DISPLAY2).
# Hardware-Regler per DDC/CI, Gamma/Schwarz per Windows-Gamma-Ramp.
param([string]$Device = "DISPLAY2")

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public class Mon {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct PHYSICAL_MONITOR { public IntPtr h; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string desc; }
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int l,t,r,b; }
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct MONITORINFOEX { public int cbSize; public RECT m; public RECT w; public uint f; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dev; }
  public delegate bool EnumProc(IntPtr hMon, IntPtr hdc, ref RECT r, IntPtr d);
  [DllImport("user32.dll")] static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr clip, EnumProc p, IntPtr d);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern bool GetMonitorInfo(IntPtr h, ref MONITORINFOEX mi);
  [DllImport("dxva2.dll")] static extern bool GetNumberOfPhysicalMonitorsFromHMONITOR(IntPtr h, out uint n);
  [DllImport("dxva2.dll")] static extern bool GetPhysicalMonitorsFromHMONITOR(IntPtr h, uint n, [Out] PHYSICAL_MONITOR[] a);
  [DllImport("dxva2.dll")] static extern bool GetVCPFeatureAndVCPFeatureReply(IntPtr h, byte code, out uint type, out uint cur, out uint max);
  [DllImport("dxva2.dll")] static extern bool SetVCPFeature(IntPtr h, byte code, uint val);
  [DllImport("gdi32.dll", CharSet=CharSet.Unicode)] static extern IntPtr CreateDC(string drv, string dev, string o, IntPtr i);
  [DllImport("gdi32.dll")] static extern bool DeleteDC(IntPtr dc);
  [DllImport("gdi32.dll")] static extern bool SetDeviceGammaRamp(IntPtr dc, ushort[] ramp);
  static IntPtr phys = IntPtr.Zero;
  public static bool Open(string dev) {
    IntPtr found = IntPtr.Zero;
    EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, (IntPtr h, IntPtr dc, ref RECT r, IntPtr d) => {
      var mi = new MONITORINFOEX(); mi.cbSize = Marshal.SizeOf(mi); GetMonitorInfo(h, ref mi);
      if (mi.dev.EndsWith(dev)) found = h; return true; }, IntPtr.Zero);
    uint n; if (!GetNumberOfPhysicalMonitorsFromHMONITOR(found, out n) || n == 0) return false;
    var a = new PHYSICAL_MONITOR[n]; GetPhysicalMonitorsFromHMONITOR(found, n, a); phys = a[0].h; return true;
  }
  public static int Get(byte code) { uint t, c, m; return GetVCPFeatureAndVCPFeatureReply(phys, code, out t, out c, out m) ? (int)c : -1; }
  public static bool Set(byte code, int v) { return SetVCPFeature(phys, code, (uint)v); }
  public static bool Ramp(string dev, ushort[] ramp) {
    IntPtr dc = CreateDC(null, @"\\.\" + dev, null, IntPtr.Zero);
    if (dc == IntPtr.Zero) return false; bool ok = SetDeviceGammaRamp(dc, ramp); DeleteDC(dc); return ok;
  }
}
"@

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfgPath = Join-Path $here "einstellungen.json"
if (-not [Mon]::Open($Device)) { [System.Windows.Forms.MessageBox]::Show("Monitor $Device nicht per DDC/CI erreichbar."); exit 1 }

$cfg = @{ Gamma = 2.4; BlackCrush = 1.2; RGain = 100; GGain = 100; BGain = 100 }
if (Test-Path $cfgPath) { (Get-Content $cfgPath -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value } }

function Set-Ramp([double]$gamma, [double]$crushPct) {
    $crush = $crushPct / 100.0
    $r = New-Object 'uint16[]' 768
    for ($i = 0; $i -lt 256; $i++) {
        $x = [Math]::Max(0.0, ($i / 255.0 - $crush) / (1.0 - $crush))
        $v = [uint16][Math]::Min(65535, [Math]::Round([Math]::Pow($x, $gamma / 2.2) * 65535))
        $r[$i] = $v; $r[$i + 256] = $v; $r[$i + 512] = $v
    }
    [Mon]::Ramp($Device, $r)
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "OLED-Look Regler – 2. Monitor"
$form.Size = New-Object System.Drawing.Size(560, 560)
$form.StartPosition = "CenterScreen"; $form.TopMost = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(24, 24, 24); $form.ForeColor = [System.Drawing.Color]::Gainsboro
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)

$status = New-Object System.Windows.Forms.Label
$status.Location = "20,470"; $status.Size = "520,24"; $status.ForeColor = [System.Drawing.Color]::Gray

$pending = @{}
$timer = New-Object System.Windows.Forms.Timer; $timer.Interval = 120
$timer.Add_Tick({
    $timer.Stop()
    foreach ($k in @($pending.Keys)) {
        $tb = $pending[$k]; $pending.Remove($k)
        & $tb.Tag.apply ($tb.Value / $tb.Tag.scale)
    }
})

$y = 20
function Add-Slider($label, $min, $max, $value, $scale, $key, [scriptblock]$apply) {
    $l = New-Object System.Windows.Forms.Label; $l.Location = "20,$script:y"; $l.Size = "170,24"; $l.Text = $label
    $v = New-Object System.Windows.Forms.Label; $v.Location = "480,$script:y"; $v.Size = "60,24"
    $tb = New-Object System.Windows.Forms.TrackBar
    $tb.Location = "190,$($script:y - 4)"; $tb.Size = "285,40"; $tb.Minimum = $min; $tb.Maximum = $max
    $tb.TickStyle = "None"; $tb.Value = [Math]::Max($min, [Math]::Min($max, [int]$value))
    $v.Text = if ($scale -ne 1) { "{0:N2}" -f ($tb.Value / $scale) } else { $tb.Value }
    $tb.Tag = @{ v = $v; scale = $scale; key = $key; apply = $apply }
    $tb.Add_ValueChanged({
        $t = $this.Tag; $val = $this.Value / $t.scale
        $t.v.Text = if ($t.scale -ne 1) { "{0:N2}" -f $val } else { $this.Value }
        $pending[$t.key] = $this
        $timer.Stop(); $timer.Start()
    })
    $form.Controls.AddRange(@($l, $tb, $v)); $script:y += 46
    return $tb
}

$sB = Add-Slider "Helligkeit (Backlight)" 0 100 ([Mon]::Get(0x10)) 1 "b" { param($x) [void][Mon]::Set(0x10, [int]$x) }
$sC = Add-Slider "Kontrast" 0 100 ([Mon]::Get(0x12)) 1 "c" { param($x) [void][Mon]::Set(0x12, [int]$x) }

$sep = New-Object System.Windows.Forms.Label; $sep.Location = "20,$y"; $sep.Size = "520,22"
$sep.Text = "Weißpunkt (schaltet Monitor auf 'Benutzer'-Farbtemperatur)"; $sep.ForeColor = [System.Drawing.Color]::Gray
$form.Controls.Add($sep); $y += 28
$userMode = { if ([Mon]::Get(0x14) -ne 0x0C) { [void][Mon]::Set(0x14, 0x0C); Start-Sleep -Milliseconds 300 } }
$sR = Add-Slider "Rot" 0 100 ([Mon]::Get(0x16)) 1 "r" { param($x) & $userMode; [void][Mon]::Set(0x16, [int]$x); $cfg.RGain = [int]$x }
$sG = Add-Slider "Grün" 0 100 ([Mon]::Get(0x18)) 1 "g" { param($x) & $userMode; [void][Mon]::Set(0x18, [int]$x); $cfg.GGain = [int]$x }
$sU = Add-Slider "Blau" 0 100 ([Mon]::Get(0x1A)) 1 "u" { param($x) & $userMode; [void][Mon]::Set(0x1A, [int]$x); $cfg.BGain = [int]$x }

$sep2 = New-Object System.Windows.Forms.Label; $sep2.Location = "20,$y"; $sep2.Size = "520,22"
$sep2.Text = "Tonkurve (Software, nur dieser Monitor)"; $sep2.ForeColor = [System.Drawing.Color]::Gray
$form.Controls.Add($sep2); $y += 28
$sGa = Add-Slider "Gamma" 200 280 ($cfg.Gamma * 100) 100 "ga" { param($x) $cfg.Gamma = $x; [void](Set-Ramp $cfg.Gamma $cfg.BlackCrush) }
$sK = Add-Slider "Schwarz-Crush %" 0 40 ($cfg.BlackCrush * 10) 10 "k" { param($x) $cfg.BlackCrush = $x; [void](Set-Ramp $cfg.Gamma $cfg.BlackCrush) }

$btnSave = New-Object System.Windows.Forms.Button; $btnSave.Text = "Speichern"; $btnSave.Location = "20,425"; $btnSave.Size = "120,34"
$btnSave.FlatStyle = "Flat"
$btnSave.Add_Click({
    $cfg.Brightness = $sB.Value; $cfg.Contrast = $sC.Value
    $cfg | ConvertTo-Json | Set-Content $cfgPath -Encoding UTF8
    $status.Text = "Gespeichert in einstellungen.json"
})
$btnBlack = New-Object System.Windows.Forms.Button; $btnBlack.Text = "Schwarzbild öffnen"; $btnBlack.Location = "150,425"; $btnBlack.Size = "170,34"
$btnBlack.FlatStyle = "Flat"
$btnBlack.Add_Click({ Start-Process (Join-Path $here "schwarz.html") })
$btnTest = New-Object System.Windows.Forms.Button; $btnTest.Text = "Testbild öffnen"; $btnTest.Location = "330,425"; $btnTest.Size = "150,34"
$btnTest.FlatStyle = "Flat"
$btnTest.Add_Click({ Start-Process (Join-Path $here "testbild.html") })

$form.Controls.AddRange(@($btnSave, $btnBlack, $btnTest, $status))
[void](Set-Ramp $cfg.Gamma $cfg.BlackCrush)
$status.Text = "Regler bewegen – Änderungen wirken sofort auf dem 2. Monitor."
[void]$form.ShowDialog()
