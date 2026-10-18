# Holt die aktuelle Schulmanager-Kopie (Code, keine Datenbank, keine .env) vom Heimserver in den Arbeitsordner des Admin-Agenten.
# Quelle: ~/schulmanager/src auf dem Server = der Stand, der dort laeuft. Ausgelassen: Lizenzserver, Tests, node_modules, .env*.
$ErrorActionPreference = "Stop"
$ziel = "$env:USERPROFILE\.openclaw\workspace-sm-admin\schulmanager-kopie"
$tmp  = "$env:TEMP\sm-kopie-$([guid]::NewGuid().ToString('N').Substring(0,6))"
New-Item -ItemType Directory -Force $tmp | Out-Null
$archiv = "$tmp\src.tgz"
# PowerShell 5.1 verfaelscht Binaerdaten in Pipes -> ueber cmd /c in eine Datei umleiten
cmd /c "ssh -o BatchMode=yes -o ConnectTimeout=15 server ""tar czf - -C ~/schulmanager/src --exclude=./lizenzserver --exclude=./tests --exclude=node_modules --exclude='.env*' --exclude='*.db' ."" > ""$archiv"""
if (-not (Test-Path $archiv) -or (Get-Item $archiv).Length -lt 100000) { throw "Kopie vom Server fehlgeschlagen (Archiv fehlt oder zu klein)." }
$neu = "$ziel.neu"
if (Test-Path $neu) { Remove-Item $neu -Recurse -Force }
New-Item -ItemType Directory -Force $neu | Out-Null
tar -xzf $archiv -C $neu
$image = (& ssh -o BatchMode=yes server "docker inspect -f '{{.Config.Image}}' schulmanager 2>/dev/null").Trim()
"Kopie vom Server geholt: $(Get-Date -Format 'yyyy-MM-dd HH:mm')`nServer-Image: $image`nQuelle: server:~/schulmanager/src (ohne lizenzserver, tests, .env, Datenbanken)" | Out-File "$neu\STAND.txt" -Encoding utf8
if (Test-Path $ziel) { Remove-Item $ziel -Recurse -Force }
Move-Item $neu $ziel
Remove-Item $tmp -Recurse -Force
Write-Host "Kopie aktualisiert: $ziel ($image)"
