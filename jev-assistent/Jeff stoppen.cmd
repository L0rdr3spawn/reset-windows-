@echo off
chcp 65001 >nul
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" jev_assistent.py --stop
timeout /t 3 >nul
