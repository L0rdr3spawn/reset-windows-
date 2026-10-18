@echo off
chcp 65001 >nul
echo Vorher den Key im Browser kopieren!
echo.
set /p P=Welcher Anbieter? (groq / gemini / openrouter) [groq]:
if "%P%"=="" set P=groq
call "%USERPROFILE%\.local\bin\ask-cheap.cmd" --set-key %P% --clipboard
echo.
call "%USERPROFILE%\.local\bin\ask-cheap.cmd" --test
echo.
pause
