@echo off
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%~dp0jev_assistent.py" --stop
timeout /t 2 >nul
