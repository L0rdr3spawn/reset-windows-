@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0gamma.ps1" -Reset
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ddc.ps1" -Action set -Code 16 -Value 70
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ddc.ps1" -Action set -Code 18 -Value 50
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ddc.ps1" -Action set -Code 20 -Value 5
