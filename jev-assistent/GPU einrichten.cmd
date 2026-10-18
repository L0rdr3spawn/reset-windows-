@echo off
rem Laedt cuBLAS fuer CUDA 12 (ca. 500 MB), damit Whisper auf der RTX 3050 statt auf der CPU laeuft.
rem Nicht waehrend eines Online-Spiels ausfuehren: der Download frisst Bandbreite.
chcp 65001 >nul
title GPU fuer Jeff einrichten
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python312"
echo Lade nvidia-cublas-cu12 (ca. 500 MB) ...
"%PY%\python.exe" -m pip install --upgrade nvidia-cublas-cu12
if errorlevel 1 (
    echo Installation fehlgeschlagen.
    pause
    exit /b 1
)
echo.
echo Fertig. Jeff wird neu gestartet und nutzt dann die RTX 3050.
call "%~dp0Jeff starten.cmd"
