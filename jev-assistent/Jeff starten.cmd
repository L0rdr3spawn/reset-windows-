@echo off
rem Jeff (neu) starten: alte Instanz beenden, Selbsttest, im Hintergrund starten, warten bis er zuhoert.
chcp 65001 >nul
title Jeff starten
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python312"
if not exist "%PY%\pythonw.exe" (
    echo Python 3.12 nicht gefunden unter %PY%
    pause
    exit /b 1
)

"%PY%\python.exe" jev_assistent.py --stop >nul
"%PY%\python.exe" selbsttest.py
if errorlevel 2 (
    echo Jeff kann so nicht starten - siehe [FEHL] oben.
    pause
    exit /b 1
)

rem Ohne Umleitung erbt Jeff die Ausgabe dieses Fensters und haelt aufrufende Programme fest
start "" "%PY%\pythonw.exe" "%~dp0jev_assistent.py" <nul >nul 2>&1
echo Jeff laedt (Whisper braucht etwa 30 Sekunden) ...
"%PY%\python.exe" jev_assistent.py --status --warten 120
if errorlevel 1 (
    echo.
    echo Jeff hoert noch nicht zu. Details stehen in jev-assistent.log.
    pause
    exit /b 1
)
echo.
"%PY%\python.exe" -c "import json;w=json.load(open('config.json',encoding='utf-8-sig')).get('weckwort','hey jeff');print('Sag: '+w+' - zum Beispiel: '+w+', wie spaet ist es')"
echo Die Testliste steht in LIESMICH.md. Dieses Fenster schliesst sich gleich.
timeout /t 15
