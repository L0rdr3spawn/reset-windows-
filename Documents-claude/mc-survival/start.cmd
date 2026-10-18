@echo off
title Survival-Server (Paper 26.2) - 127.0.0.1:25540
cd /d "%~dp0"
"%APPDATA%\PrismLauncher\java\java-runtime-epsilon\bin\java.exe" -Xms2G -Xmx4G -jar paper-26.2-129.jar --nogui
pause
