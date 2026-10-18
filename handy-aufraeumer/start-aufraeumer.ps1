# Startet den lokalen KI-Aufraeumer fuer Handy (llama.cpp + Qwen3-4B) - ausschliesslich auf der RTX 3050.
# Wird per Autostart (versteckt) ausgefuehrt. Handy spricht ihn an unter http://127.0.0.1:8091/v1
$ErrorActionPreference = 'Stop'
$dir    = $PSScriptRoot
$server = Join-Path $dir 'llama\llama-server.exe'
$modell = Join-Path $dir 'modell\Qwen3-4B-Instruct-2507-Q4_K_M.gguf'
$port   = 8091
$karte  = 'RTX 3050'
$log    = Join-Path $dir 'aufraeumer.log'

# Laeuft schon? Dann nichts tun.
try { Invoke-RestMethod "http://127.0.0.1:$port/health" -TimeoutSec 2 | Out-Null; exit 0 } catch {}

# Grafikkarte per Name suchen (die Nummer VulkanN kann sich aendern)
$geraet = (& $server --list-devices 2>&1 | Select-String "^\s*(Vulkan\d+):.*$karte").Matches | Select-Object -First 1
if (-not $geraet) {
    "$(Get-Date -f s) FEHLER: $karte nicht gefunden - Aufraeumer startet NICHT (kein Ausweichen auf andere Karte)" | Add-Content $log
    exit 1
}
$dev = $geraet.Groups[1].Value
# Nur diese eine Karte fuer Vulkan sichtbar machen -> andere Karten werden gar nicht erst angefasst.
# Danach ist sie innerhalb des Servers "Vulkan0".
$env:GGML_VK_VISIBLE_DEVICES = $dev -replace '\D', ''

$argumente = @('-m', "`"$modell`"", '--device', 'Vulkan0', '-ngl', '99', '-c', '4096',
               '--host', '127.0.0.1', '--port', $port, '--alias', 'qwen3-4b', '-np', '1')
"$(Get-Date -f s) Start auf $dev ($karte)" | Add-Content $log
Start-Process -FilePath $server -ArgumentList $argumente -WindowStyle Hidden `
    -RedirectStandardError (Join-Path $dir 'server-stderr.log') -RedirectStandardOutput (Join-Path $dir 'server-stdout.log')
