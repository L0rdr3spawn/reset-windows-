@echo off
rem Begleiter-Bot starten: Manager frisch starten (neuer Code), dann Minecraft 26.3 mit der Botlink-Mod.
rem Im Spiel: Pausenmenue "Bot holen" (Singleplayer) bzw. Mehrspieler-Knopf / "/bot join", Taste B = Einstellungen,
rem Taste G = Ziel/Block/folgen, /bot hilfe = alle Befehle.
rem "START.cmd nurbot" startet nur den Manager (ohne Minecraft).
cd /d "%~dp0"
where node >nul 2>nul || (echo Node.js fehlt - bitte installieren: https://nodejs.org & pause & exit /b 1)
if not exist node_modules (echo Installiere Abhaengigkeiten ... & call npm install --no-fund --no-audit || (pause & exit /b 1))
echo Stoppe alten Manager, falls er laeuft ...
node bc.js stop
echo Starte Manager ...
node bc.js status >nul || (echo Manager startet nicht - siehe daten\manager.log & pause & exit /b 1)
echo Manager laeuft auf 127.0.0.1:47811.
if /i "%~1"=="nurbot" goto ende
set "PRISM=%LOCALAPPDATA%\Programs\PrismLauncher\prismlauncher.exe"
if exist "%PRISM%" (
  echo Starte Minecraft 26.3 ...
  start "" "%PRISM%" --launch 26.3
) else (
  echo Prism Launcher nicht gefunden - Minecraft 26.3 bitte selbst starten.
)
:ende
echo Fertig. Dieses Fenster schliesst sich gleich.
ping -n 4 127.0.0.1 >nul
