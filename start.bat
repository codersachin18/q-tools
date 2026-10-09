@echo off
rem  Q-Tools launcher - double click to open the app.
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app.py"
    exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%~dp0app.py"
    exit /b 0
)

where python.exe >nul 2>nul
if not errorlevel 1 (
    start "" /min python.exe "%~dp0app.py"
    exit /b 0
)

echo.
echo  Python was not found. Run setup.bat first.
echo.
pause
exit /b 1
