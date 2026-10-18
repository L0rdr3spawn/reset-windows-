@echo off
cd /d "%~dp0"
"%APPDATA%\PrismLauncher\java\java-runtime-epsilon\bin\java.exe" -Xms2G -Xmx4G -jar paper.jar --nogui
pause
