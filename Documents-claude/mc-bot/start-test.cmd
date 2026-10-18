@echo off
rem Bot auf dem lokalen Testserver (mc-testserver, Port 25566)
cd /d "%~dp0"
node bot.js config-test.json
pause
