param([string]$Action="read",[int]$Code=0,[int]$Value=0,[string]$Device="DISPLAY2")
$src = @"
using System; using System.Runtime.InteropServices;
public class DDC {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct PHYSICAL_MONITOR { public IntPtr h; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string desc; }
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int l,t,r,b; }
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct MONITORINFOEX { public int cbSize; public RECT m; public RECT w; public uint f; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dev; }
  public delegate bool EnumProc(IntPtr hMon, IntPtr hdc, ref RECT r, IntPtr d);
  [DllImport("user32.dll")] public static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr clip, EnumProc p, IntPtr d);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern bool GetMonitorInfo(IntPtr h, ref MONITORINFOEX mi);
  [DllImport("dxva2.dll", SetLastError=true)] public static extern bool GetNumberOfPhysicalMonitorsFromHMONITOR(IntPtr h, out uint n);
  [DllImport("dxva2.dll")] public static extern bool GetPhysicalMonitorsFromHMONITOR(IntPtr h, uint n, [Out] PHYSICAL_MONITOR[] a);
  [DllImport("dxva2.dll")] public static extern bool GetVCPFeatureAndVCPFeatureReply(IntPtr h, byte code, out uint type, out uint cur, out uint max);
  [DllImport("dxva2.dll")] public static extern bool SetVCPFeature(IntPtr h, byte code, uint val);
  [DllImport("dxva2.dll")] public static extern bool DestroyPhysicalMonitors(uint n, PHYSICAL_MONITOR[] a);
  public static IntPtr Find(string dev) {
    IntPtr found = IntPtr.Zero;
    EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, (IntPtr h, IntPtr dc, ref RECT r, IntPtr d) => {
      var mi = new MONITORINFOEX(); mi.cbSize = Marshal.SizeOf(mi); GetMonitorInfo(h, ref mi);
      if (mi.dev.EndsWith(dev)) found = h; return true; }, IntPtr.Zero);
    return found;
  }
  public static IntPtr Phys(string dev) {
    IntPtr h = Find(dev); uint n; bool ok = GetNumberOfPhysicalMonitorsFromHMONITOR(h, out n);
    var a = new PHYSICAL_MONITOR[n]; GetPhysicalMonitorsFromHMONITOR(h, n, a); return a[0].h;
  }
}
"@
Add-Type -TypeDefinition $src
$ErrorActionPreference="Stop"; $p = [DDC]::Phys($Device)
$names = @{0x10='Helligkeit';0x12='Kontrast';0x14='Farbpreset';0x16='Rot-Gain';0x18='Gruen-Gain';0x1A='Blau-Gain';0x6C='Rot-Black';0x6E='Gruen-Black';0x70='Blau-Black';0x87='Schaerfe';0x8A='Saettigung';0x72='Gamma';0xDC='Bildmodus';0x0B='FarbtempStep';0x0C='FarbtempReq'}
if ($Action -eq "read") {
  foreach ($c in ($names.Keys | Sort-Object)) { $t=0;$cur=0;$max=0
    $ok=[DDC]::GetVCPFeatureAndVCPFeatureReply($p,[byte]$c,[ref]$t,[ref]$cur,[ref]$max)
    "{0,-13} 0x{1:X2}: {2}" -f $names[$c],$c,($(if($ok){"$cur / $max"}else{"n/a"})) }
} else {
  $ok=[DDC]::SetVCPFeature($p,[byte]$Code,[uint32]$Value); "set 0x{0:X2}={1}: {2}" -f $Code,$Value,$ok
}
