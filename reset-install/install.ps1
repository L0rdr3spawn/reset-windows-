# Neuinstallation nach dem Reset. Als Administrator starten:
#   powershell -ExecutionPolicy Bypass -File install.ps1
# Ablauf: Grundlagen -> Programme -> Browser aufraeumen -> Python-Libs -> Handarbeit-Liste

$ErrorActionPreference = 'Continue'
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrator')) {
    Write-Host 'Bitte als Administrator starten.' -ForegroundColor Red; exit 1
}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host 'winget fehlt: "App Installer" im Microsoft Store aktualisieren und neu starten.' -ForegroundColor Red; exit 1
}

function Install($id, $name, $source = 'winget') {
    Write-Host ">> $name" -ForegroundColor Cyan
    winget install --id $id -e --source $source --silent --accept-package-agreements --accept-source-agreements
}

# ---------- 1. Grundlagen (Abhaengigkeiten) ----------
Write-Host '=== Grundlagen ===' -ForegroundColor Yellow
Install 'Microsoft.VCRedist.2015+.x64'        'Visual C++ Runtime x64 (fast jedes Spiel/Programm)'
Install 'Microsoft.VCRedist.2015+.x86'        'Visual C++ Runtime x86 (aeltere Programme, z. B. Afterburner)'
Install 'Microsoft.DirectX'                   'DirectX End-User Runtime (Spiele)'
Install 'Microsoft.EdgeWebView2Runtime'       'WebView2 (Obsidian-Plugins, Discord, Claude-App)'
Install 'Microsoft.DotNet.DesktopRuntime.8'   '.NET 8 Desktop (FanControl, OpenRGB-Tools)'
Install 'Microsoft.DotNet.DesktopRuntime.9'   '.NET 9 Desktop'
Install 'namazso.PawnIO'                      'PawnIO (Sensor-/Lueftertreiber fuer HWiNFO, FanControl)'
Install 'Git.Git'                             'Git (Claude Code braucht es unter Windows)'
Install 'Python.Python.3.12'                  'Python 3.12'

# ---------- 2. Programme ----------
Write-Host '=== Programme ===' -ForegroundColor Yellow
Install 'Brave.Brave'                         'Brave (Standardbrowser)'
Install 'Google.Chrome'                       'Chrome (nur fuer Claude in Chrome)'
Install 'Microsoft.VisualStudioCode'          'VS Code'
Install 'Anthropic.Claude'                    'Claude (Desktop-App)'
Install 'Anthropic.ClaudeCode'                'Claude Code'
Install 'ElementLabs.LMStudio'                'LM Studio'
Install 'Discord.Discord'                     'Discord'
Install 'Obsidian.Obsidian'                   'Obsidian'
Install 'PrismLauncher.PrismLauncher'         'Prism Launcher'
Install 'cjpais.Handy'                        'Handy (Diktat)'
Install 'RevoUninstaller.RevoUninstaller'     'Revo Uninstaller'
Install 'REALiX.HWiNFO'                       'HWiNFO'
Install 'Rem0o.FanControl'                    'FanControl'
Install 'OpenRGB.OpenRGB'                     'OpenRGB'
Install 'Guru3D.Afterburner'                  'MSI Afterburner'
Install 'Guru3D.RTSS'                         'RivaTuner (gehoert zu Afterburner, FPS-Overlay)'
Install 'SteelSeries.GG'                      'SteelSeries GG'
Install 'Valve.Steam'                         'Steam (Spiele neu laden)'
Install 'RARLab.WinRAR'                       'WinRAR'
Install 'VideoLAN.VLC'                        'VLC'
Install 'OBSProject.OBSStudio'                'OBS Studio'
Install 'Proton.ProtonVPN'                    'Proton VPN'
Install 'Proton.ProtonMail'                   'Proton Mail'
Install 'Microsoft.PowerToys'                 'PowerToys'
Install 'voidtools.Everything'                'Everything (Dateisuche)'
Install 'GitHub.cli'                          'GitHub CLI (gh)'
Install 'GitHub.GitHubDesktop'                'GitHub Desktop'

# ---------- 2b. Pentesting ----------
Write-Host '=== Pentesting ===' -ForegroundColor Yellow
Install 'GlassWire.GlassWire'                 'GlassWire (Netzwerk-Monitor/Firewall)'
Install 'Insecure.Nmap'                       'Nmap (bringt Npcap + Zenmap + ncat mit)'
Install 'WiresharkFoundation.Wireshark'       'Wireshark'
Install 'PortSwigger.BurpSuite.Community'     'Burp Suite Community (Web-Proxy)'
Install 'ZAP.ZAP'                             'OWASP ZAP (Web-Scanner, Alternative/Ergaenzung zu Burp)'
Install 'mitmproxy.mitmproxy'                 'mitmproxy (HTTPS-Mitschnitt auf der Konsole)'
Install 'ffuf.ffuf'                           'ffuf (Verzeichnis-/Parameter-Fuzzing)'
Install 'WerWolv.ImHex'                       'ImHex (Hex-Editor fuer Reverse Engineering)'
Install 'PuTTY.PuTTY'                         'PuTTY (SSH/Serial)'
Install 'Microsoft.Sysinternals.Suite'        'Sysinternals (Process Explorer, Autoruns, ...)'
Write-Host '>> WSL + Kali Linux (John the Ripper, hashcat, Metasploit, hydra, sqlmap, gobuster ...)' -ForegroundColor Cyan
wsl --install --no-distribution
Install 'OffSec.KaliLinux'                    'Kali Linux (WSL-Distro)'
Install 'XP8CLZL93F5Z4P'                      'NVIDIA App (installiert den Grafiktreiber mit)' 'msstore'

# ---------- 3. Browser aufraeumen ----------
Write-Host '=== Browser aufraeumen ===' -ForegroundColor Yellow
foreach ($id in 'Opera.Opera', 'Opera.OperaGX', 'Mozilla.Firefox') {
    winget uninstall --id $id -e --silent 2>$null | Out-Null
}
# Edge laesst sich unter Windows 11 nicht sauber entfernen (Systemkomponente) -> bleibt, aber ohne Standard/Autostart
$edgePol = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'
New-Item $edgePol -Force | Out-Null
Set-ItemProperty $edgePol -Name StartupBoostEnabled -Value 0 -Type DWord
Set-ItemProperty $edgePol -Name BackgroundModeEnabled -Value 0 -Type DWord
# Brave als Standard: Windows 11 erlaubt das nur per Klick -> Einstellungsseite oeffnen
Start-Process 'ms-settings:defaultapps?registeredAppUser=Brave'
# Claude in Chrome: Seite oeffnen, dort "Zu Chrome hinzufuegen" klicken
Start-Process 'https://claude.ai/chrome'

# ---------- 4. Python-Libs (Vorschlag, schlank) ----------
Write-Host '=== Python-Libs ===' -ForegroundColor Yellow
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (Test-Path $py) {
    & $py -m pip install --upgrade pip
    & $py -m pip install requests httpx rich python-dotenv pyyaml yt-dlp pywin32
}

# ---------- 5. Handarbeit ----------
Write-Host @'

=== Muss von Hand (kein winget-Paket) ===
 1. Brave als Standard: im geoeffneten Fenster "Brave" bei HTTP/HTTPS/.html waehlen.
 2. Claude in Chrome: Erweiterung auf claude.ai/chrome hinzufuegen und anmelden.
 3. Handy: Einstellungen -> Modell -> "Whisper Medium" herunterladen.
 4. Rovyl:      Installer von der Rovyl-Seite (auf dem Heimserver/Stick: Backup-Ordner)
 5. Womier-Treiber: Installer von der Womier-Webseite (WOMIER Driver)
 6. Plasticity: Installer + Lizenz von plasticity.xyz (Konto)
 7. NVIDIA: Nach der NVIDIA App den Treiber dort installieren lassen, Neustart.
 8. Steam: nach dem Login die Spiele neu laden (oder aus den Zips auf dem Heimserver entpacken).
 9. Kali: nach dem Neustart 'kali' starten, Benutzer anlegen, dann:
      sudo apt update && sudo apt install -y kali-tools-top10 john hashcat hydra sqlmap gobuster seclists
    (hashcat nutzt in WSL keine NVIDIA-GPU zuverlaessig -> fuer GPU-Cracking Windows-Version von hashcat.net holen.)
10. John the Ripper fuer Windows (optional): Release von github.com/openwall/john-packages.
'@



