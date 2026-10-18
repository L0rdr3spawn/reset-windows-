@echo off
echo Stelle Kalibrierung wieder her...
set P=powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ddc.ps1" -Action set
%P% -Code 20 -Value 12 & timeout /t 2 >nul
%P% -Code 22 -Value 50 & timeout /t 2 >nul
%P% -Code 24 -Value 46 & timeout /t 2 >nul
%P% -Code 26 -Value 38 & timeout /t 2 >nul
%P% -Code 16 -Value 40 & timeout /t 2 >nul
%P% -Code 18 -Value 50 & timeout /t 2 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0gamma.ps1" -Gamma 2.6 -BlackCrush 0.015
echo Fertig.
timeout /t 3 >nul
